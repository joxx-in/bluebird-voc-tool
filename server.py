import http.server
import socketserver
import json
import subprocess
import os
import re
import threading
import webbrowser
import sys
from urllib.parse import urlparse, parse_qs

PORT = 18765

# ── ADB 유틸 ─────────────────────────────────────────────────────────────────

def find_adb():
    local = os.path.join(
        os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__),
        'adb.exe'
    )
    return local if os.path.exists(local) else 'adb'

def run_adb(*args, timeout=8):
    try:
        r = subprocess.run([find_adb()] + list(args), capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except FileNotFoundError:
        return '__ADB_NOT_FOUND__', -1
    except subprocess.TimeoutExpired:
        return '__TIMEOUT__', -2

def get_connected_devices():
    out, _ = run_adb('devices', '-l')
    if out == '__ADB_NOT_FOUND__':
        return None, 'adb_not_found'
    devices = []
    for line in out.splitlines()[1:]:
        line = line.strip()
        if not line or 'offline' in line:
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == 'device':
            sid = parts[0]
            model = next((p.split(':', 1)[1] for p in parts if p.startswith('model:')), '')
            devices.append({'id': sid, 'model': model})
    return devices, None

def getprop(device_id, prop):
    out, _ = run_adb('-s', device_id, 'shell', 'getprop', prop)
    return out.strip()

def collect_device_info(device_id):
    props = {
        'serial_no':      getprop(device_id, 'ro.serialno'),
        'model':          getprop(device_id, 'ro.product.model'),
        'manufacturer':   getprop(device_id, 'ro.product.manufacturer'),
        'android_ver':    getprop(device_id, 'ro.build.version.release'),
        'sdk':            getprop(device_id, 'ro.build.version.sdk'),
        'build_id':       getprop(device_id, 'ro.build.display.id'),
        'firmware':       getprop(device_id, 'ro.build.version.incremental'),
        'build_date':     getprop(device_id, 'ro.build.date'),
        'security_patch': getprop(device_id, 'ro.build.version.security_patch'),
        'fingerprint':    getprop(device_id, 'ro.build.fingerprint'),
        'item_sn':        getprop(device_id, 'ro.vendor.bluebird.item_sn'),
        'model_sn':       getprop(device_id, 'ro.vendor.bluebird.model_sn'),
        'chipset':        getprop(device_id, 'ro.board.platform'),
        'cpu_abi':        getprop(device_id, 'ro.product.cpu.abi'),
        'wifi_mac': '', 'bt_mac': '', 'imei1': '', 'imei2': '',
        'battery_level': '', 'battery_cycle': '', 'battery_temp': '',
        'total_ram': '', 'total_storage': '', 'used_storage': '',
    }
    ro_sn = props['serial_no']
    item  = props['item_sn']
    props['full_sn'] = ro_sn if ro_sn else (f"{props['model_sn']} {item}".strip() if item else '')

    mac_out, _ = run_adb('-s', device_id, 'shell', 'cat', '/sys/class/net/wlan0/address')
    if mac_out and 'No such' not in mac_out:
        props['wifi_mac'] = mac_out.strip()

    bt_out, _ = run_adb('-s', device_id, 'shell', 'settings', 'get', 'secure', 'bluetooth_address')
    if bt_out and bt_out != 'null':
        props['bt_mac'] = bt_out.strip()

    imei_out, _ = run_adb('-s', device_id, 'shell', 'service', 'call', 'phone', '1', 's16', 'com.android.phone')
    imei_match = re.findall(r"'([0-9]{15})'", imei_out)
    if len(imei_match) >= 1: props['imei1'] = imei_match[0]
    if len(imei_match) >= 2: props['imei2'] = imei_match[1]

    # 배터리 상세
    bat_out, _ = run_adb('-s', device_id, 'shell', 'dumpsys', 'battery')
    lv = re.search(r'level:\s*(\d+)', bat_out)
    if lv: props['battery_level'] = lv.group(1) + '%'
    tmp = re.search(r'temperature:\s*(\d+)', bat_out)
    if tmp: props['battery_temp'] = str(int(tmp.group(1)) / 10) + '°C'
    cyc = re.search(r'Charge cycle count:\s*(\d+)', bat_out)
    if cyc: props['battery_cycle'] = cyc.group(1) + '회'

    # RAM
    mem_out, _ = run_adb('-s', device_id, 'shell', 'cat', '/proc/meminfo')
    total_m = re.search(r'MemTotal:\s+(\d+)', mem_out)
    if total_m:
        props['total_ram'] = str(round(int(total_m.group(1)) / 1024 / 1024, 1)) + ' GB'

    # Storage
    df_out, _ = run_adb('-s', device_id, 'shell', 'df', '/data')
    df_m = re.search(r'\S+\s+(\d+)\s+(\d+)\s+(\d+)', df_out)
    if df_m:
        total_kb = int(df_m.group(1))
        used_kb  = int(df_m.group(2))
        props['total_storage'] = str(round(total_kb / 1024 / 1024, 1)) + ' GB'
        props['used_storage']  = str(round(used_kb  / 1024 / 1024, 1)) + ' GB'

    return props

# ── 로그 파서 ─────────────────────────────────────────────────────────────────

LOG_PATTERNS = {
    'model':          r'\[ro\.product\.model\]\s*:\s*\[([^\]]+)\]',
    'manufacturer':   r'\[ro\.product\.manufacturer\]\s*:\s*\[([^\]]+)\]',
    'android_ver':    r'\[ro\.build\.version\.release\]\s*:\s*\[([^\]]+)\]',
    'sdk':            r'\[ro\.build\.version\.sdk\]\s*:\s*\[([^\]]+)\]',
    'build_id':       r'\[ro\.build\.display\.id\]\s*:\s*\[([^\]]+)\]',
    'firmware':       r'\[ro\.build\.version\.incremental\]\s*:\s*\[([^\]]+)\]',
    'build_date':     r'\[ro\.build\.date\]\s*:\s*\[([^\]]+)\]',
    'security_patch': r'\[ro\.build\.version\.security_patch\]\s*:\s*\[([^\]]+)\]',
    'fingerprint':    r'\[ro\.build\.fingerprint\]\s*:\s*\[([^\]]+)\]',
    'item_sn':        r'\[ro\.vendor\.bluebird\.item_sn\]\s*:\s*\[([^\]]+)\]',
    'model_sn':       r'\[ro\.vendor\.bluebird\.model_sn\]\s*:\s*\[([^\]]+)\]',
    'chipset':        r'\[ro\.board\.platform\]\s*:\s*\[([^\]]+)\]',
    'cpu_abi':        r'\[ro\.product\.cpu\.abi\]\s*:\s*\[([^\]]+)\]',
    'wifi_mac':       r'\[vendor\.wlan\.intf1\.mac\.address\]\s*:\s*\[([^\]]+)\]',
    'serial_no':      r'\[ro\.serialno\]\s*:\s*\[([^\]]+)\]',
    'sim_state':      r'\[gsm\.sim\.state\]\s*:\s*\[([^\]]+)\]',
    'battery_level':  r'healthd: battery l=(\d+)',
    'battery_temp':   r'healthd: battery l=\d+ v=\d+ t=([\d.]+)',
    'battery_voltage':r'healthd: battery l=\d+ v=(\d+)',
    'battery_cycle':  r'Charge cycle count:\s*(\d+)',
    'total_ram':      r'MemTotal:\s+(\d+)\s+kB',
}

CHUNK = 512 * 1024

def parse_content(content: str, filename_hint: str = '') -> dict:
    result = {}
    crashes = []
    anrs = []
    tombstones = []
    boot_events = []
    found = set()
    total = len(content)
    overlap = 2048

    # 파일명에서 날짜 추출
    log_date = ''
    date_m = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', filename_hint)
    if date_m:
        log_date = f"{date_m.group(1)}-{date_m.group(2)}-{date_m.group(3)} {date_m.group(4)}:{date_m.group(5)}:{date_m.group(6)}"
    # 로그 첫 줄 타임스탬프에서도 추출 시도
    if not log_date:
        ts_m = re.search(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', content[:2000])
        if ts_m:
            log_date = ts_m.group(1)

    offset = 0
    while offset < total:
        end = min(offset + CHUNK, total)
        chunk = content[offset:end]

        # 기본 프로퍼티 파싱
        for key, pat in LOG_PATTERNS.items():
            if key not in found:
                m = re.search(pat, chunk)
                if m:
                    result[key] = m.group(1)
                    found.add(key)

        # FATAL EXCEPTION + Stack Trace 전체
        if len(crashes) < 10:
            for m in re.finditer(
                r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)[^\n]*FATAL EXCEPTION[^\n]*\n'
                r'[^\n]*Process:\s*(\S+)[^\n]*\n'
                r'((?:(?!\d{2}-\d{2} \d{2}:\d{2}:\d{2})[^\n]*\n){0,30})',
                chunk, re.MULTILINE
            ):
                if len(crashes) < 10:
                    stack = m.group(3).strip()
                    lines = [l.strip() for l in stack.splitlines() if l.strip()]
                    exception_line = lines[0] if lines else ''
                    at_lines = [l for l in lines if l.startswith('at ') or l.startswith('Caused by:')][:8]
                    crashes.append({
                        'time':      m.group(1),
                        'process':   m.group(2),
                        'exception': exception_line,
                        'stacktrace': at_lines,
                    })

        # ANR 탐지
        if len(anrs) < 5:
            for m in re.finditer(
                r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)[^\n]*ANR in\s+(\S+)[^\n]*\n'
                r'(?:[^\n]*Reason:\s*([^\n]+))?',
                chunk
            ):
                if len(anrs) < 5:
                    anrs.append({
                        'time':    m.group(1),
                        'process': m.group(2),
                        'reason':  m.group(3).strip() if m.group(3) else '',
                    })

        # Tombstone (Native Crash)
        if len(tombstones) < 5:
            for m in re.finditer(
                r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)[^\n]*'
                r'(Fatal signal \d+[^\n]*|SIGSEGV[^\n]*)',
                chunk
            ):
                if len(tombstones) < 5:
                    tombstones.append({
                        'time':   m.group(1),
                        'signal': m.group(2).strip(),
                    })

        # Boot 이벤트
        if len(boot_events) < 3:
            for m in re.finditer(
                r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)[^\n]*'
                r'(Boot completed|boot_completed|sys\.boot_completed)',
                chunk
            ):
                if len(boot_events) < 3:
                    boot_events.append({'time': m.group(1)})

        core = {'model', 'android_ver', 'firmware', 'item_sn'}
        all_crash_done = len(crashes) >= 5 or 'FATAL EXCEPTION' not in content[offset:end]
        if core.issubset(found) and len(anrs) > 0:
            pass  # 계속 스캔 (crash/anr 더 찾기)

        offset = end - overlap if end < total else total

    # 후처리
    ro_sn   = result.get('serial_no', '')
    item    = result.get('item_sn', '')
    model_s = result.get('model_sn', '')
    result['full_sn'] = ro_sn if ro_sn else (f"{model_s} {item}".strip() if item else '')

    mac = result.get('wifi_mac', '')
    if mac and ':' not in mac and len(mac) == 12:
        result['wifi_mac'] = ':'.join(mac[i:i+2] for i in range(0, 12, 2))

    # RAM 단위 변환
    if 'total_ram' in result:
        try:
            result['total_ram'] = str(round(int(result['total_ram']) / 1024 / 1024, 1)) + ' GB'
        except:
            pass

    # 배터리
    if 'battery_level' in result:
        result['battery_level'] = result['battery_level'] + '%'
    if 'battery_temp' in result:
        result['battery_temp'] = result['battery_temp'] + '°C'
    if 'battery_cycle' in result:
        result['battery_cycle'] = result['battery_cycle'] + '회'

    result['crashes']    = crashes
    result['anrs']       = anrs
    result['tombstones'] = tombstones
    result['boot_events']= boot_events
    result['log_date']   = log_date

    return result


# ── HTTP 핸들러 ───────────────────────────────────────────────────────────────

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        p = urlparse(self.path)
        if p.path == '/':
            here = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
            with open(os.path.join(here, 'index.html'), 'rb') as f:
                body = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
        elif p.path == '/api/devices':
            devices, err = get_connected_devices()
            self.send_json({'error': 'adb_not_found'} if err == 'adb_not_found' else {'devices': devices or []})
        elif p.path == '/api/device_info':
            qs = parse_qs(p.query)
            dev_id = qs.get('id', [''])[0]
            if not dev_id:
                self.send_json({'error': 'no device id'}, 400); return
            self.send_json(collect_device_info(dev_id))
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        p = urlparse(self.path)
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        if p.path == '/api/parse_log':
            try:
                data = json.loads(raw)
                content  = data.get('content', '')
                filename = data.get('filename', '')
                result = parse_content(content, filename)
                self.send_json(result)
            except Exception as e:
                self.send_json({'error': str(e)}, 500)
        else:
            self.send_response(404); self.end_headers()


def open_browser():
    import time; time.sleep(0.9)
    webbrowser.open(f'http://localhost:{PORT}')

if __name__ == '__main__':
    print(f'[VOC Tool] 서버 시작 → http://localhost:{PORT}')
    print(f'[VOC Tool] 브라우저가 자동으로 열립니다...')
    print(f'[VOC Tool] 종료하려면 이 창을 닫으세요.')
    threading.Thread(target=open_browser, daemon=True).start()
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        httpd.allow_reuse_address = True
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('[VOC Tool] 종료')

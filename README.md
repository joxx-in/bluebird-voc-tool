# bluebird-voc-tool

Android 단말 로그 파일을 파싱하거나 ADB로 직접 연결해 VOC 입력 항목을 자동으로 채워주는 도구.

단말 정보 수집에 걸리던 5~10분을 10초 이하로 줄입니다.

**배포:** https://splendid-clafoutis-fa9f16.netlify.app

---

## 배경

블루버드 FAE 업무에서 VOC 접수 시 아래 항목을 매번 수작업으로 입력해야 했습니다.

```
Device Serial Number / OS Version / Firmware / Build ID /
Security Patch / Chipset / Wi-Fi MAC / IMEI / Crash Log
```

이 정보는 이미 단말 로그(`event.log`)에 다 있었습니다.  
정규식으로 파싱하면 되는 일을 왜 눈으로 찾고 있었는지가 출발점이었습니다.

---

## 개발 과정

### 1. 문제 발견 — 로그 파일 분석

VOC 접수 건마다 15~30MB 로그 파일을 텍스트 에디터로 열고, 필요한 값을 눈으로 찾아서 복사했습니다.

로그를 직접 분석해보니 `event.log`(Android getprop dump)에 필요한 정보가 모두 구조화된 형태로 있었습니다.

```
[ro.product.model]              : S50
[ro.build.version.release]      : 12
[ro.build.version.incremental]  : BB_R1.17_0325
[ro.vendor.bluebird.item_sn]    : A5LAWB
[vendor.wlan.intf1.mac.address] : 00:16:7F:44:95:FC
```

정규식으로 파싱하면 5~10분 작업이 1초로 줄어든다는 걸 확인했습니다.

### 2. 파서 구현 — Python + 정규식

Python 표준 라이브러리만으로 로컬 HTTP 서버를 구성하고, 브라우저에서 로그 파일을 업로드하면 파싱 결과를 반환하는 구조를 만들었습니다.

15~30MB 파일을 한 번에 처리하면 브라우저가 멈추는 문제가 있어서 512KB 청크 단위로 나눠 파싱하고, 핵심 정보를 모두 찾으면 조기 종료하는 방식으로 해결했습니다.

### 3. ADB 연동 — S/N 전체 수집

로그 파싱만으로는 S/N 뒷자리 숫자를 가져올 수 없었습니다. Android 보안 정책상 `ro.serialno`가 일반 앱의 getprop dump에 노출되지 않도록 설계되어 있기 때문입니다.

USB로 연결된 단말에서 ADB로 직접 `getprop ro.serialno`를 호출하는 방식으로 해결했습니다. 배터리 사이클, RAM, 스토리지 사용량도 이 시점에 함께 수집합니다.

### 4. Windows 소켓 오류 수정

처음에는 대용량 파일 처리를 위해 SSE(Server-Sent Events) 스트리밍 방식으로 구현했는데, Windows에서 `ConnectionAbortedError: [WinError 10053]`이 발생했습니다.

Python 표준 `http.server`가 Windows에서 `Transfer-Encoding: chunked`를 제대로 지원하지 않는 문제였습니다. SSE를 걷어내고 단순 POST → JSON 응답 방식으로 교체해 해결했습니다.

### 5. UI 개선 — Toss 스타일

초기 다크모드 UI는 글자가 작고 가독성이 낮았습니다. Pretendard + JetBrains Mono 폰트, 라이트모드, 카드 기반 레이아웃으로 전면 교체했습니다.

### 6. VOC 폼 구성 — 탭 분리

기기 정보 확인과 VOC 작성을 하나의 화면에서 처리하다 보니 UX가 복잡했습니다. 탭을 분리하고 VOC 11개 항목 중 자동으로 채울 수 있는 항목(S/N, OS/FW, 로그 취득 시각, Crash 로그)은 자동으로, 나머지는 직접 입력하는 구조로 정리했습니다.

Issue Category는 사내 VOC 시스템의 실제 드롭다운 항목과 동일하게 맞췄습니다.

### 7. 상세 분석 탭 추가

단순 정보 수집을 넘어 개발팀이 이슈를 분석하는 데 필요한 정보를 추가했습니다.

- FATAL EXCEPTION + Stack Trace 전체 (최대 8줄)
- ANR (Application Not Responding) 자동 감지
- Native Crash / Tombstone (SIGSEGV) 감지
- 배터리 잔량 / 온도 / 충전 사이클
- RAM, 스토리지 사용량
- 로그 취득 시각 (파일명 또는 첫 타임스탬프에서 추출)
- 다중 단말 비교 (로그 세트 여러 개 동시 분석)

### 8. 웹 배포 + 사용 통계

팀원 전체가 쓰려면 각자 Python을 설치하고 서버를 실행해야 하는 진입 장벽이 있었습니다.

브라우저 JS만으로 로그 파싱이 가능하다는 점을 활용해 Netlify에 정적 배포했습니다. ADB 연결이 필요한 경우에만 로컬에서 `server.py`를 실행하면 됩니다.

팀 전체 사용 현황 파악을 위해 Supabase를 연동했습니다. VOC 복사 시점에 모델명, OS 버전, 카테고리, Crash 건수를 자동으로 기록하고, Admin 탭에서 비밀번호 인증 후 통계를 확인할 수 있습니다.

---

## 동작 방식

```
로그 파일 업로드 (또는 USB ADB 연결)
  → Android 시스템 프로퍼티 파싱
  → VOC 항목 자동 완성
  → 클립보드 복사
  → VOC 시스템에 붙여넣기
```

**로그에서 자동으로 읽어오는 항목**

- Serial Number (`ro.serialno`, `ro.vendor.bluebird.item_sn`)
- Android 버전, SDK, Firmware, Build ID, 보안 패치
- Chipset, CPU ABI, Wi-Fi MAC, IMEI
- FATAL EXCEPTION + Stack Trace
- ANR (Application Not Responding)
- Native Crash (Tombstone, SIGSEGV)
- 배터리 잔량 / 온도 / 충전 사이클
- RAM, 스토리지 사용량
- 로그 취득 시각

---

## 실행

웹 버전 (로그 파싱):
```
https://splendid-clafoutis-fa9f16.netlify.app
```

ADB 연동이 필요한 경우 (로컬 실행):
```bash
# adb.exe를 같은 폴더에 복사 후
python server.py
# → http://localhost:18765 브라우저 자동 실행
```

Python이 없는 PC에 배포할 경우:
```bash
pip install pyinstaller
python build_exe.py
# → dist/VOC툴.exe 생성
```

ADB 다운로드: https://developer.android.com/tools/releases/platform-tools

---

## 구조

```
server.py      Python 로컬 서버 (ADB 연동 + 로그 파서)
index.html     브라우저 UI (4탭 + Admin)
build_exe.py   PyInstaller 빌드 스크립트
```

서버(`server.py`)는 Python 표준 라이브러리만 사용합니다. 외부 패키지 의존성이 없습니다.

---

## 파싱 대상 로그

| 파일 | 포함 정보 |
|---|---|
| `event.log` | System Properties (모델, OS, FW, MAC 등) |
| `main.log` | Crash, ANR, 앱 동작 |
| `kernel.log` | 부팅 정보, 드라이버 |
| `.qdb` | Radio / 모뎀 상태 |

---

## 개발 이력

**v1.0** — 로그 파싱 기본 구현, Python 서버 + 브라우저 UI 구조 수립

**v1.1** — ADB 연동 추가 (S/N 전체 수집), Windows 소켓 오류 수정 (SSE → 단순 POST),  
512KB 청크 파싱으로 15~30MB 대용량 파일 처리

**v1.2** — UI 전면 교체 (Pretendard + JetBrains Mono, Toss 스타일 라이트모드)

**v1.3** — VOC 탭 분리 (기기 정보 / VOC 작성), Issue Category 드롭다운,  
클립보드 복사 1클릭

**v1.4** — 상세 분석 탭 추가 (Stack Trace 전체, ANR, Native Crash, 배터리 사이클,  
RAM/스토리지, 로그 취득 시각, 다중 단말 비교), 히스토리 저장 탭 추가

**v1.5** — Netlify 배포, Supabase 연동 (사용 통계 자동 수집),  
Admin 탭 추가 (비밀번호 인증 + 대시보드)

---

## 기술 스택

- Python 3.x — 표준 라이브러리 (`http.server`, `subprocess`, `re`)
- Vanilla JS — 프레임워크 없음
- Android ADB — `getprop`, `dumpsys battery`, `df /data`
- 정규식 기반 청크 파싱
- Supabase — 사용 통계 저장 (PostgreSQL)
- Netlify — 정적 호스팅

# bluebird-voc-tool

Android 단말 로그 파일을 파싱하거나 ADB로 직접 연결해 VOC 입력 항목을 자동으로 채워주는 도구.

단말 정보 수집에 걸리던 5~10분을 10초 이하로 줄입니다.

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
index.html     브라우저 UI
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

---

## 기술 스택

- Python 3.x — 표준 라이브러리 (`http.server`, `subprocess`, `re`)
- Vanilla JS — 프레임워크 없음
- Android ADB — `getprop`, `dumpsys battery`, `df /data`
- 정규식 기반 청크 파싱

---

## 배포

https://splendid-clafoutis-fa9f16.netlify.app

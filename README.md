# 🔧 Bluebird VOC Auto-fill Tool

> **현업 FAE가 직접 정의하고 개발한 단말 정보 수집 자동화 툴**  
> A field automation tool built by a FAE to eliminate repetitive VOC data entry

<br>

[![Made by FAE](https://img.shields.io/badge/Made%20by-FAE%20Engineer-3182f6?style=flat-square)](https://github.com/your-github-id)
[![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Android ADB](https://img.shields.io/badge/Android-ADB-3ddc84?style=flat-square&logo=android&logoColor=white)](https://developer.android.com/tools/adb)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?style=flat-square&logo=windows&logoColor=white)](https://www.microsoft.com/windows)

---

## 📌 Problem — 왜 만들었나

Bluebird FAE2팀은 고객사 이슈 접수 시 아래 항목을 **매번 수동으로 수집·입력**해야 했습니다.

```
Device Serial Number / OS Version / Firmware / Build ID /
Security Patch / Chipset / Wi-Fi MAC / IMEI / Crash Log ...
```

| 기존 프로세스 | 문제점 |
|---|---|
| 단말에서 설정 앱 직접 확인 | 항목마다 화면 이동 필요, 오타 발생 |
| 로그 파일 수동 열람 | 15~30MB 파일에서 필요한 값을 눈으로 탐색 |
| VOC 시스템에 수동 입력 | 건당 평균 **5~10분** 소요 |
| 이슈 급증 시 | 처리 지연 → 고객사 응대 품질 저하 |

**→ "로그 파일이 있는데 왜 직접 찾아야 하지?" 라는 의문에서 출발했습니다.**

---

## ✅ Solution — 어떻게 해결했나

```
로그 파일 업로드 (또는 USB ADB 연결)
        ↓
핵심 정보 자동 파싱 / 수집
        ↓
VOC 양식 자동 완성
        ↓
클립보드 복사 → VOC 시스템에 붙여넣기
```

### 주요 기능

| 기능 | 설명 |
|---|---|
| **로그 파싱** | `event.log`, `main.log`, `kernel.log` 등 다중 파일 동시 파싱 |
| **ADB 자동 수집** | USB 연결된 단말에서 S/N, OS, FW 등 실시간 추출 |
| **Crash 자동 감지** | `FATAL EXCEPTION` 자동 탐지 및 VOC 항목에 반영 |
| **VOC 폼 자동 완성** | 11개 항목 중 자동 입력 가능한 항목 즉시 채움 |
| **클립보드 복사** | 1클릭으로 전체 VOC 내용 복사 |
| **진행률 표시** | 대용량 로그 처리 시 실시간 파싱 진행률 표시 |

---

## 📊 Impact — 효과

| 지표 | Before | After |
|---|---|---|
| 단말 정보 수집 시간 | 5 ~ 10분 | **10초 이하** |
| VOC 항목 수동 입력 | 10개 항목 전체 | **자동 입력 3개 + 수동 입력 8개** |
| 로그에서 Crash 탐색 | 수동 (15~30MB 파일 열람) | **자동 감지 및 추출** |
| 오타·누락 가능성 | 높음 | **거의 없음** |

---

## 🏗 Architecture

```
┌─────────────────────────────────────┐
│         Browser (index.html)        │
│  - Toss-style UI (Pretendard font)  │
│  - 기기 정보 탭 / VOC 작성 탭       │
│  - Drag & Drop 파일 업로드           │
│  - 실시간 VOC 미리보기              │
└──────────────┬──────────────────────┘
               │ HTTP (localhost:18765)
┌──────────────▼──────────────────────┐
│      Python Local Server            │
│      (http.server + socketserver)   │
│                                     │
│  ┌─────────────┐  ┌──────────────┐  │
│  │ Log Parser  │  │  ADB Bridge  │  │
│  │ (Regex)     │  │  (subprocess)│  │
│  └─────────────┘  └──────────────┘  │
└─────────────────────────────────────┘
               │
    ┌──────────▼──────────┐
    │   Android Device    │
    │   (USB ADB)         │
    └─────────────────────┘
```

### 파싱 대상 로그 타입

| 파일 | 포함 정보 |
|---|---|
| `event.log` | System Properties (모델, OS, FW, MAC 등) |
| `main.log` | Logcat Main (Crash, ANR, 앱 동작) |
| `kernel.log` | Kernel 메시지, 부팅 정보 |
| `radio.log` / `.qdb` | 모뎀, 통신 상태 |
| `tcpdump.pcap` | 네트워크 패킷 (또는 Crash 로그) |

---

## 🛠 Tech Stack

| 영역 | 기술 |
|---|---|
| Backend | Python 3.9+ (표준 라이브러리만 사용, 외부 의존성 없음) |
| Frontend | Vanilla HTML / CSS / JavaScript |
| UI 스타일 | Toss 스타일 (Pretendard + JetBrains Mono) |
| ADB 연동 | Android Debug Bridge (`subprocess` 호출) |
| 로그 파싱 | 정규식 기반 멀티파일 청크 파싱 |
| 배포 형태 | 로컬 실행 (`.py` 더블클릭 또는 `.exe` 빌드) |

---

## 🗂 개발 이력 (CHANGELOG)

### v1.3 — VOC 폼 탭 분리 (2025.10)
- 기기 정보 탭 / VOC 작성 탭 분리
- VOC 11개 항목 폼 구현 (자동 입력 + 직접 입력)
- 실시간 VOC 미리보기 + 클립보드 복사

### v1.2 — UI 전면 리디자인 (2025.10)
- Toss 스타일 라이트모드 UI 적용
- Pretendard + JetBrains Mono 폰트 도입
- 대형 타이포그래피 + 카드 기반 레이아웃

### v1.1 — ADB 연동 + 성능 개선 (2025.10)
- USB ADB 직접 수집 기능 추가 (S/N 전체 포함)
- SSE 스트리밍 → 안정적인 단순 POST 방식으로 교체 (Windows 호환성)
- 청크 파싱으로 대용량 로그 처리 (15~30MB)
- 파싱 진행률 바 추가

### v1.0 — 최초 구현 (2025.09)
- 로그 파일 파싱 기본 구현
- Python 로컬 서버 + 브라우저 UI 구조 수립
- 추출 항목: 모델, OS, FW, MAC, SIM, 배터리, Crash

---

## 🚀 설치 및 실행

### 방법 1 — Python으로 바로 실행 (권장)

```bash
# 1. 이 저장소 클론
git clone https://github.com/your-github-id/bluebird-voc-tool.git
cd bluebird-voc-tool

# 2. adb.exe 준비 (Windows)
# https://developer.android.com/tools/releases/platform-tools
# 다운로드 후 이 폴더에 adb.exe 복사

# 3. 실행
python server.py
# → 브라우저가 자동으로 열립니다
```

### 방법 2 — .exe 빌드 (Python 없는 PC 배포용)

```bash
pip install pyinstaller
python build_exe.py
# → dist/VOC툴.exe 생성
# → dist/ 폴더에 adb.exe 함께 배치
```

### 방법 3 — 웹 데모 (ADB 없이 로그 파싱만)

👉 **[Live Demo](https://your-netlify-url.netlify.app)** ← Netlify 배포 후 링크 추가

---

## 📁 파일 구조

```
bluebird-voc-tool/
├── server.py          # Python 로컬 서버 (ADB + 로그 파서)
├── index.html         # 브라우저 UI
├── build_exe.py       # PyInstaller 빌드 스크립트
├── 실행방법.txt        # 비개발자용 안내서
├── docs/
│   ├── problem.md     # 문제 정의 상세
│   ├── architecture.md
│   └── screenshots/   # UI 스크린샷
└── README.md
```

---

## 💡 배경 & 인사이트

이 프로젝트는 단순한 사이드 프로젝트가 아닙니다.

- **문제를 직접 발견** — 회사 지시가 아닌, 반복 업무에서 비효율을 직접 인식
- **도메인 지식 활용** — Android 로그 구조, ADB 프로토콜, Bluebird 단말 프로퍼티 체계를 현업 경험으로 파악
- **사용자 중심 설계** — "PC 못 다루는 동료도 더블클릭 하나로 쓸 수 있어야 한다"는 기준으로 UX 설계
- **지속적 개선** — 실제 사용하면서 나온 오류(Windows 소켓 오류, 대용량 파일 처리 등)를 반복 수정

> *"같은 일을 두 번 하기 싫어서 만들었고, 만들고 나니 팀 전체가 빨라졌습니다."*

---

## 👤 만든 사람

**Kim Jong-in (Ethan)** — FAE2 팀 주임, Bluebird  
Field Application Engineering · Project Management · Technical Sales  
Android 단말 전문 (OS 5.1 ~ 15), RFID, 산업용 모바일 솔루션

📧 Contact: [GitHub Profile](https://github.com/your-github-id)

---

<div align="center">
  <sub>Built with 🔧 by a FAE who got tired of copy-pasting</sub>
</div>

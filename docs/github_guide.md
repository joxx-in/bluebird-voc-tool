# GitHub 업로드 & 배포 가이드

## 1단계 — GitHub 저장소 생성

1. https://github.com 로그인
2. 우상단 `+` → **New repository**
3. 설정:
   - Repository name: `bluebird-voc-tool`
   - Description: `FAE 업무 자동화 — Android 단말 정보 자동 수집 및 VOC 자동완성 툴`
   - **Public** 선택 (포트폴리오용)
   - ☑ Add a README file → 체크 해제 (우리가 직접 올릴 것)
4. **Create repository** 클릭

---

## 2단계 — 로컬에서 Git 초기화 후 업로드

```bash
# voc_tool 폴더로 이동
cd C:\Users\user\Downloads\voc_tool

# Git 초기화
git init

# .gitignore 생성 (불필요한 파일 제외)
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo "dist/" >> .gitignore
echo "build/" >> .gitignore
echo "*.spec" >> .gitignore

# README.md 복사 (이 패키지에 포함된 것 사용)
# docs/ 폴더도 함께 복사

# 파일 전체 추가
git add .

# 첫 커밋
git commit -m "feat: initial release v1.0 - log parser + ADB integration + VOC form"

# GitHub 저장소 연결 (your-github-id 부분을 본인 ID로 변경)
git remote add origin https://github.com/your-github-id/bluebird-voc-tool.git

# 업로드
git branch -M main
git push -u origin main
```

---

## 3단계 — 웹 데모 배포 (Netlify, 무료)

ADB 없이 **로그 파싱 기능만** 브라우저에서 동작하는 데모 버전을 배포합니다.

### 3-1. 데모용 index_demo.html 준비

`index.html`에서 ADB 관련 부분만 비활성화한 버전을 별도로 만들어두면 됩니다.
(서버 없이 브라우저만으로 동작 — `server.py` 없이 JS만으로 파싱)

### 3-2. Netlify 배포

1. https://netlify.com 가입 (GitHub 계정 연동)
2. **Add new site** → **Import an existing project**
3. GitHub 저장소 선택 → `bluebird-voc-tool`
4. Build settings:
   - Build command: 비워두기
   - Publish directory: `.` (루트)
5. **Deploy site** 클릭
6. 자동 생성된 URL을 README의 Live Demo 링크에 추가

---

## 4단계 — GitHub 저장소 꾸미기

### Topics 추가 (검색 노출용)
저장소 페이지 → About 옆 ⚙️ → Topics:
```
android, adb, automation, fae, python, voc, log-parser, field-engineering
```

### README 배지 수정
README.md 상단 배지의 `your-github-id` 부분을 실제 GitHub ID로 교체

### Releases 태그 추가
```bash
git tag -a v1.3.0 -m "VOC form tab + Toss-style UI"
git push origin v1.3.0
```
GitHub에서 Releases → Create release → 태그 선택 → 설명 작성

---

## 5단계 — 포트폴리오 활용 방법

### GitHub Profile README에 추가
`https://github.com/your-github-id/your-github-id` 저장소의 README.md에:

```markdown
### 🔧 주요 프로젝트
| 프로젝트 | 설명 | 기술 |
|---|---|---|
| [VOC Auto-fill Tool](https://github.com/your-github-id/bluebird-voc-tool) | FAE 업무 자동화 — 단말 정보 수집 자동화 | Python · ADB · JS |
```

### 이력서/LinkedIn에 기재 방법
```
[사이드 프로젝트] VOC 자동완성 툴 개발 (2025.09 ~ 10)
- FAE 업무에서 단말 정보 수동 수집 프로세스를 자동화
- Android 로그 파싱 + ADB 연동으로 수집 시간 5~10분 → 10초 이하로 단축
- Python 로컬 서버 + Vanilla JS UI 직접 설계·구현
- GitHub: https://github.com/your-github-id/bluebird-voc-tool
```

---

## 파일 구성 최종 확인

GitHub에 올라가야 하는 파일:

```
bluebird-voc-tool/
├── README.md          ✅ 포트폴리오 핵심
├── server.py          ✅ Python 백엔드
├── index.html         ✅ 브라우저 UI
├── build_exe.py       ✅ EXE 빌드 스크립트
├── 실행방법.txt        ✅ 비개발자용 안내
├── .gitignore         ✅ 불필요 파일 제외
└── docs/
    ├── problem.md     ✅ 문제 정의 상세
    └── architecture.md
```

올리지 말아야 할 것:
- `dist/` (빌드 결과물)
- `__pycache__/`
- `*.log` (실제 로그 파일 — 보안상)

"""
PyInstaller 빌드 스크립트
실행: python build_exe.py
결과: dist/VOC툴/ 폴더 안에 VOC툴.exe + index.html + adb.exe(있으면)
"""
import subprocess, sys, os, shutil

# index.html을 exe와 같은 폴더에 배포
cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--onefile',
    '--noconsole',
    '--name', 'VOC툴',
    '--add-data', 'index.html;.',   # Windows 구분자
    'server.py'
]

print('[빌드] PyInstaller 실행 중...')
r = subprocess.run(cmd, check=False)
if r.returncode != 0:
    print('[오류] 빌드 실패. pip install pyinstaller 후 재시도하세요.')
    sys.exit(1)

print('[빌드] 완료! dist/VOC툴.exe 생성됨')
print('[안내] adb.exe를 dist/ 폴더에 넣어주세요.')

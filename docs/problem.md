# 📌 Problem Definition

## 배경

Bluebird FAE2팀은 산업용 모바일 단말(PDA, 스마트폰, 결제 단말기)을 고객사에 납품하고,
현장에서 발생하는 기술 이슈를 접수·분석·해결하는 업무를 담당합니다.

이슈 발생 시 VOC(Voice of Customer) 시스템에 아래 항목을 기입해야 합니다:

```
1. Customer / Partner
2. Device Serial Number
3. OS / FW Version
4. Issue Category
5. Issue Description / Video link
7. Step to Reproduce
8. Issue related logs
9. Total deployed / Failure devices
10. Failure Rate
11. Shipping / Manufacturing Date
```

## 문제의 핵심

단말 1대의 정보를 수집하려면:

1. 단말 직접 조작 → 설정 > 단말 정보 (여러 화면 이동)
2. 로그 파일 취득 앱 실행 → 6가지 타입 로그 수집
3. 15~30MB 로그 파일을 텍스트 에디터로 열고 직접 검색
4. S/N, OS, FW, MAC 등 각 항목을 수동으로 복사·입력
5. Crash가 있으면 로그에서 직접 찾아서 옮겨 적기

**단말 1대 기준 약 5~10분 소요**

## 왜 이게 문제인가

- 이슈 1건이 아니라 동일 현장에서 **여러 대**가 동시에 문제가 생기면 처리 시간이 선형으로 증가
- 사람이 직접 옮겨 적으면 **오타·누락** 발생
- 로그 파일에 이미 정보가 있는데 **눈으로 찾아야 하는** 비효율
- FAE의 시간이 정보 수집에 낭비되면 **실제 이슈 분석 시간이 줄어듦**

## 도메인 인사이트

Android 단말의 `event.log`(getprop dump)에는 아래가 모두 포함됩니다:

```
[ro.product.model]              : S50
[ro.build.version.release]      : 12
[ro.build.version.incremental]  : BB_R1.17_0325
[ro.vendor.bluebird.item_sn]    : A5LAWB
[vendor.wlan.intf1.mac.address] : 00:16:7F:44:95:FC
...
```

이걸 **정규식으로 파싱**하면 5~10분 작업이 1초로 줄어듭니다.

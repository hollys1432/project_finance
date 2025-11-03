# Render Cron Job 설정 가이드

Render에서 매일 자동으로 주식 데이터를 업데이트하는 Cron Job을 설정하는 방법입니다.

---

## 📋 Cron Job이란?

- 정해진 시간에 자동으로 실행되는 작업
- 주식 데이터를 매일 자동으로 업데이트하는 데 사용
- Render 무료 플랜에서도 사용 가능! ✅

---

## 🚀 단계별 설정 방법

### Step 1: Render Dashboard 접속

1. [Render Dashboard](https://dashboard.render.com) 로그인
2. 좌측 상단 **"New +"** 버튼 클릭
3. 드롭다운 메뉴에서 **"Cron Job"** 선택

![New Cron Job 버튼](https://render.com/docs/images/...)

---

### Step 2: GitHub 저장소 연결

**Option A: 기존 저장소 선택**
- Web Service와 동일한 저장소가 목록에 표시됨
- 해당 저장소 선택 후 **"Connect"** 클릭

**Option B: 새 저장소 연결**
- "Connect a repository" 클릭
- GitHub 계정 인증
- 저장소 선택

---

### Step 3: 기본 정보 입력

#### Name (필수)
```
daily-stock-update
```
또는 원하는 이름 (예: `stock-data-updater`)

#### Region (필수)
⚠️ **중요: Web Service와 같은 지역 선택!**
- Singapore
- Oregon (US West)
- Frankfurt
- 등등

**이유:** 같은 지역에 있어야 빠르고 안정적

#### Branch (필수)
```
main
```
또는 배포하는 브랜치 이름

---

### Step 4: Build & Start Commands

#### Runtime
```
Python 3
```

#### Build Command
```bash
pip install -r requirements.txt
```

**설명:**
- 필요한 패키지 설치
- Django, pandas, yfinance 등

#### Command (필수 - 실제 실행 명령어)
```bash
python manage.py daily_update
```

**이 명령어가 실제로 실행됩니다!**

---

### Step 5: Schedule 설정 (중요!)

Cron 표현식을 사용하여 실행 시간 설정:

#### 기본 포맷
```
분 시 일 월 요일
*  *  *  *  *
```

#### 추천 스케줄

**매일 오후 6시 (UTC 기준)**
```
0 18 * * *
```
- 한국 시간: 다음날 오전 3시 (UTC+9)
- 미국 동부: 오후 1시 또는 2시 (EST/EDT)

**매일 오전 9시 (UTC 기준)**
```
0 9 * * *
```
- 한국 시간: 오후 6시
- 미국 동부: 오전 4시 또는 5시

**평일만 오후 5시 (UTC)**
```
0 17 * * 1-5
```
- 월~금요일만 실행
- 주말 제외

**매주 월요일 오전 8시 (UTC)**
```
0 8 * * 1
```

#### Cron 표현식 도우미

온라인 도구 사용: [Crontab Guru](https://crontab.guru/)
- 원하는 시간 입력
- Cron 표현식 자동 생성
- 한국어 설명 제공

---

### Step 6: 환경 변수 설정

**Environment** 탭으로 이동하여 환경 변수 추가:

#### 필수 환경 변수

```env
SECRET_KEY=<Web Service와 동일한 값>
DEBUG=False
DATABASE_URL=<Web Service와 동일한 PostgreSQL URL>
```

#### 빠른 방법: Web Service 환경 변수 그룹 연결

1. Environment 탭에서 **"Add from Service"** 클릭
2. Web Service 선택
3. 모든 환경 변수 자동 복사됨 ✅

**이 방법이 가장 쉽습니다!**

---

### Step 7: 생성 완료

1. 모든 설정 확인
2. **"Create Cron Job"** 버튼 클릭
3. Cron Job 생성 및 첫 실행 예약

---

## 🔍 Cron Job 확인 및 모니터링

### 실행 로그 확인

1. Render Dashboard → 생성한 Cron Job 선택
2. **"Logs"** 탭 클릭
3. 실행 로그 실시간 확인

**성공적인 실행 로그 예시:**
```
=========================================
일일 데이터 업데이트 시작: 2025-11-03 18:00:00
=========================================

현재 등록된 기업 수: 한국 5개, 미국 7개

[1/2] 한국 주식 데이터 업데이트 중...
✓ 한국 주식 업데이트 완료

[2/2] 미국 주식 데이터 업데이트 중...
✓ 미국 주식 업데이트 완료

=========================================
일일 데이터 업데이트 완료!
=========================================

📊 업데이트 결과:
  ✓ 한국 주식: 성공
  ✓ 미국 주식: 성공

⏱️  소요 시간: 45.3초
🕐 완료 시각: 2025-11-03 18:00:45
```

### 다음 실행 시간 확인

- Cron Job 페이지 상단에 "Next run" 표시됨
- 예: "Next run: in 23 hours"

### 수동 실행 (테스트용)

1. Cron Job 페이지에서 **"Trigger Deploy"** 클릭
2. 즉시 실행되며 Logs에서 확인 가능

---

## ⚙️ Cron Job 설정 예시

### 예시 1: 무료 플랜 - 매일 업데이트

```yaml
Name: daily-stock-update
Region: Singapore
Branch: main
Runtime: Python 3

Build Command: pip install -r requirements.txt
Command: python manage.py daily_update

Schedule: 0 18 * * *

Environment:
  - SECRET_KEY=<your-key>
  - DEBUG=False
  - DATABASE_URL=<postgres-url>
```

### 예시 2: 평일만 업데이트

```yaml
Name: weekday-stock-update
Region: Oregon (US West)
Branch: main
Runtime: Python 3

Build Command: pip install -r requirements.txt
Command: python manage.py daily_update

Schedule: 0 17 * * 1-5  # 월~금요일만

Environment:
  - (Web Service와 동일)
```

### 예시 3: 한국/미국 따로 업데이트

**Cron Job 1: 한국 주식**
```yaml
Name: kr-stock-update
Command: python manage.py daily_update --skip-us
Schedule: 0 9 * * *  # 한국 시간 오후 6시
```

**Cron Job 2: 미국 주식**
```yaml
Name: us-stock-update
Command: python manage.py daily_update --skip-kr
Schedule: 0 22 * * *  # 미국 동부 시간 오후 5시/6시
```

---

## 🚨 문제 해결

### Cron Job이 실행되지 않음

**확인 사항:**
1. Schedule 형식이 올바른지 확인
2. Branch가 올바른지 확인
3. Logs에서 에러 메시지 확인

### 실행은 되지만 에러 발생

**확인 사항:**
1. 환경 변수가 올바르게 설정되었는지
2. DATABASE_URL이 올바른지
3. Web Service와 같은 Region인지

**Logs에서 에러 확인:**
```
✗ 한국 주식 업데이트 실패: could not connect to server
```

**해결 방법:**
- DATABASE_URL 확인
- PostgreSQL 서비스 상태 확인

### 빌드는 성공하지만 명령어 실행 실패

**원인:**
- `requirements.txt`에 필요한 패키지 누락
- 명령어 오타

**해결:**
```bash
# Build Command가 성공했는지 확인
# Command가 정확한지 확인
python manage.py daily_update
```

---

## 💰 비용

### 무료 플랜
- **Cron Job은 무료입니다!** ✅
- 실행 시간만큼만 과금
- 짧은 작업은 무료 범위 내

### 유료 플랜
- 더 긴 실행 시간
- 더 많은 리소스

---

## 📊 실행 시간 참고

| 작업 | 예상 시간 |
|------|-----------|
| 주요 종목 12개 업데이트 | ~30초 |
| 한국 전체 업데이트 | ~5분 |
| 미국 S&P500 업데이트 | ~10분 |

---

## 🎯 권장 설정

### 무료 플랜 사용자

```yaml
Name: daily-stock-update
Command: python manage.py daily_update
Schedule: 0 18 * * *  # 매일 UTC 오후 6시
```

**이유:**
- 간단하고 명확
- 짧은 실행 시간
- 무료 범위 내

### 많은 데이터 수집 시

```yaml
Name: daily-kr-update
Command: python manage.py daily_update --skip-us
Schedule: 0 9 * * *

---

Name: daily-us-update
Command: python manage.py daily_update --skip-kr
Schedule: 0 22 * * *
```

**이유:**
- 한국/미국 시장 시간에 맞춰 분산
- 각각의 실행 시간 단축

---

## ✅ 설정 완료 체크리스트

- [ ] Cron Job 생성 완료
- [ ] Schedule 설정 확인
- [ ] 환경 변수 연결 확인
- [ ] "Next run" 시간 확인
- [ ] 수동 실행으로 테스트
- [ ] Logs에서 성공 확인

---

## 📚 추가 정보

- [Render Cron Jobs 공식 문서](https://render.com/docs/cronjobs)
- [Crontab 표현식 가이드](https://crontab.guru/)

---

이제 매일 자동으로 최신 주식 데이터가 업데이트됩니다! 🎉

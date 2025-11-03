# Render 자동 데이터 수집 가이드

Render에서 주식 데이터를 자동으로 수집하는 방법을 설명합니다.

---

## 🎯 3가지 자동화 방법

### 방법 1: 빌드 시 자동 수집 (권장하지 않음 ❌)
### 방법 2: Render Shell에서 수동 초기화 (권장 ⭐)
### 방법 3: Cron Job으로 정기 업데이트 (필수 ✅)

---

## 방법 1: 빌드 시 자동 수집 ❌

**장점:**
- 배포 직후 바로 데이터 사용 가능

**단점:**
- 빌드 시간이 매우 길어짐 (1~2시간)
- 빌드 타임아웃 발생 가능
- 매 배포마다 재수집 (비효율적)
- API 호출 제한 위험

**사용 방법:**

1. Render Dashboard → Web Service → Environment 탭
2. 환경 변수 추가:

```
# 빠른 초기화 (주요 종목, 1년치)
INIT_DATA=true
INIT_MODE=quick
```

또는

```
# 전체 초기화 (3년치) - 매우 오래 걸림!
INIT_DATA=true
INIT_MODE=full
```

3. Deploy 또는 Manual Deploy 실행

**초기화 모드:**
- `quick`: 주요 종목, 1년치 (~100 MB, 15분 소요)
- `kr-only`: 한국만 (~490 MB)
- `us-only`: 미국만 (~48 MB)
- `full` (기본값): 전체 3년치 (~700 MB, 1~2시간 소요)

⚠️ **경고:** 빌드 타임아웃으로 실패할 수 있으므로 권장하지 않습니다.

---

## 방법 2: Render Shell에서 수동 초기화 ⭐ (권장)

**장점:**
- 빌드 타임아웃 없음
- 진행 상황 실시간 확인
- 필요할 때만 실행
- 안전하고 확실함

**사용 방법:**

### Step 1: Render 배포 완료 후

1. Render Dashboard → 해당 Web Service 선택
2. 상단 메뉴에서 **"Shell"** 클릭
3. Shell 창이 열리면 다음 명령어 실행

### Step 2: 초기 데이터 로딩

**옵션 A: 빠른 초기화 (권장, 무료 플랜)**
```bash
python manage.py init_data --quick
```
- 주요 종목만 (한국 5개, 미국 7개)
- 1년치 데이터
- 약 10~20 MB
- 소요 시간: 약 5~10분

**옵션 B: 한국 전체 (KOSPI만)**
```bash
python manage.py init_data --kr-markets "KOSPI" --skip-us
```
- KOSPI 전체, 3년치
- 약 200~300 MB
- 소요 시간: 약 30~60분

**옵션 C: 미국 주요 종목만**
```bash
python manage.py init_data --skip-kr --us-symbols "AAPL,GOOGL,MSFT,TSLA,NVDA,AMZN,META,NFLX,INTC,AMD"
```
- 미국 주요 10개 종목, 3년치
- 약 5~10 MB
- 소요 시간: 약 5~10분

**옵션 D: 전체 초기화 (유료 플랜 권장)**
```bash
python manage.py init_data
```
- 한국 전체 + 미국 S&P500/NASDAQ100
- 약 700 MB
- 소요 시간: 약 1~2시간

**옵션 E: 기존 데이터가 있어도 강제 실행**
```bash
python manage.py init_data --quick --force
```

### Step 3: 진행 상황 확인

Shell에서 실시간으로 진행 상황이 표시됩니다:
```
==========================================
초기 데이터 로딩 시작
==========================================

[1/4] 한국 기업 정보 수집 중...
✓ 한국 기업 정보 수집 완료

[2/4] 한국 가격 데이터 수집 중...
[1/5] 005930 삼성전자 : 2024-01-01 ~ 2025-01-01 (365일)
  2024-01-01~2024-12-31: 250건
✓ 한국 가격 데이터 수집 완료

...
```

---

## 방법 3: Cron Job으로 정기 업데이트 ✅ (필수)

초기 데이터를 로딩한 후, 매일 자동으로 최신 데이터를 업데이트합니다.

### Step 1: Render Cron Job 생성

1. Render Dashboard → "New +" → "Cron Job" 선택
2. 다음과 같이 설정:

**기본 정보:**
- Name: `daily-stock-update` (원하는 이름)
- Environment: `Python 3`
- Region: Web Service와 동일한 지역
- Branch: `main`

**빌드 설정:**
- Build Command: `pip install -r requirements.txt`
- Command: `python manage.py daily_update`

**스케줄:**
- Schedule: `0 18 * * *` (매일 오후 6시, UTC 기준)
  - 한국 시간 기준: `0 9 * * *` (매일 오전 6시 KST)
  - 미국 동부 시간 기준: `0 22 * * *` (매일 오후 5시 EST)

**환경 변수:**
- Web Service와 동일한 환경 변수 연결 (DATABASE_URL 등)

### Step 2: 환경 변수 설정 (Web Service와 동일)

Cron Job의 Environment 탭에서:
```
SECRET_KEY=<your-secret-key>
DEBUG=False
ALLOWED_HOSTS=.render.com
DATABASE_URL=<PostgreSQL Internal URL>
```

### Step 3: Cron Job 생성 및 확인

1. "Create Cron Job" 클릭
2. Logs 탭에서 실행 로그 확인
3. 다음 실행 예정 시각 확인

### Cron 스케줄 예제

```bash
# 매일 오후 6시 (UTC)
0 18 * * *

# 매일 오전 6시 (UTC) - 한국 오후 3시
0 6 * * *

# 평일만 오후 5시 (UTC)
0 17 * * 1-5

# 매주 월요일 오전 9시 (UTC)
0 9 * * 1

# 매시간 정각
0 * * * *
```

**참고:** [Crontab 생성기](https://crontab.guru/)

---

## 📋 명령어 상세 옵션

### init_data (초기 데이터 로딩)

```bash
python manage.py init_data [OPTIONS]

옵션:
  --quick              빠른 초기화 (주요 종목, 1년치)
  --skip-kr            한국 주식 건너뛰기
  --skip-us            미국 주식 건너뛰기
  --kr-markets MARKETS 한국 시장 지정 (예: KOSPI,KOSDAQ)
  --us-symbols SYMBOLS 미국 종목 지정 (예: AAPL,GOOGL,MSFT)
  --force              기존 데이터가 있어도 강제 실행
```

**예제:**
```bash
# 빠른 초기화
python manage.py init_data --quick

# 한국 KOSPI만
python manage.py init_data --skip-us --kr-markets "KOSPI"

# 미국 FAANG만
python manage.py init_data --skip-kr --us-symbols "META,AAPL,AMZN,NFLX,GOOGL"

# 기존 데이터 무시하고 재수집
python manage.py init_data --force
```

### daily_update (일일 업데이트)

```bash
python manage.py daily_update [OPTIONS]

옵션:
  --skip-kr     한국 주식 업데이트 건너뛰기
  --skip-us     미국 주식 업데이트 건너뛰기
  --verbose     상세 로그 출력
```

**예제:**
```bash
# 전체 업데이트
python manage.py daily_update

# 미국만 업데이트
python manage.py daily_update --skip-kr

# 상세 로그 포함
python manage.py daily_update --verbose
```

---

## 🔍 문제 해결

### 빌드 타임아웃 발생
**증상:** 빌드가 10~15분 후 타임아웃
**해결:**
- `INIT_DATA=true` 제거
- Render Shell에서 수동으로 `init_data` 실행

### Cron Job이 실행되지 않음
**확인 사항:**
1. Cron Job의 Logs 탭에서 에러 확인
2. 환경 변수 (특히 DATABASE_URL) 설정 확인
3. 스케줄 형식이 올바른지 확인
4. Cron Job과 Web Service가 같은 Region인지 확인

### API 호출 제한
**증상:** 수집 중 에러 발생, 일부 종목 누락
**해결:**
- 다시 실행 (증분 수집으로 누락된 부분만 수집됨)
- `--sleep-min`, `--sleep-max` 값 증가
- 종목 수를 줄여서 여러 번 나눠 실행

### 데이터베이스 용량 초과
**해결:**
```python
# Shell에서 실행
python manage.py shell

from datetime import date, timedelta
from stocks.models import PriceData, USPriceData

# 2년 이전 데이터 삭제
cutoff = date.today() - timedelta(days=2*365)
PriceData.objects.filter(date__lt=cutoff).delete()
USPriceData.objects.filter(date__lt=cutoff).delete()
```

---

## 📊 권장 설정 요약

### 무료 플랜 (1GB DB)
```bash
# 초기화
python manage.py init_data --quick

# Cron Job
매일 실행: python manage.py daily_update
```
**예상 용량:** ~20 MB

### 유료 플랜 ($7/월, 10GB DB)
```bash
# 초기화
python manage.py init_data --kr-markets "KOSPI" --skip-us

# 또는
python manage.py init_data --us-symbols "AAPL,GOOGL,..." --skip-kr

# Cron Job
매일 실행: python manage.py daily_update
```
**예상 용량:** ~300~500 MB

---

## 🎯 최종 권장 워크플로우

1. **초기 배포**
   - `INIT_DATA` 환경 변수 설정하지 않음
   - 배포 완료 후 빠르게 시작

2. **Render Shell에서 초기 데이터 로딩**
   ```bash
   python manage.py init_data --quick
   ```
   - 진행 상황 확인 가능
   - 안전하고 확실함

3. **Cron Job 설정**
   - 매일 자동 업데이트
   - 최신 데이터 유지

4. **모니터링**
   - Cron Job Logs 주기적으로 확인
   - 에러 발생 시 Shell에서 수동 실행

이 방법이 가장 안전하고 효율적입니다! 🚀

# 로컬에서 프로덕션 DB 연결 가이드

Render 무료 버전은 Shell이 제공되지 않고, Yahoo Finance API가 Render 서버 IP를 차단하는 경우가 많습니다.
따라서 **로컬 환경에서 Render의 프로덕션 데이터베이스에 직접 연결**하여 데이터를 수집하는 것이 가장 안정적입니다.

---

## 📋 목차

1. [Render External Database URL 확인](#1-render-external-database-url-확인)
2. [로컬 환경 설정](#2-로컬-환경-설정)
3. [데이터 수집 실행](#3-데이터-수집-실행)
4. [데이터 확인](#4-데이터-확인)
5. [일일 자동 업데이트 설정](#5-일일-자동-업데이트-설정)
6. [문제 해결](#6-문제-해결)

---

## 1. Render External Database URL 확인

### 단계 1: Render Dashboard 접속

1. [Render Dashboard](https://dashboard.render.com/) 로그인
2. **PostgreSQL** 인스턴스 선택
3. **Info** 탭에서 다음 정보 확인:

### 단계 2: External Database URL 복사

**External Database URL** 형식:
```
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

**예시:**
```
postgresql://finance_user:abc123XYZ456@dpg-xxxxxxxxxxxxx-a.oregon-postgres.render.com:5432/finance_db
```

⚠️ **주의:**
- **Internal Database URL**이 아닌 **External Database URL**을 사용하세요
- `Internal`은 Render 서비스 간 통신용, `External`은 외부 연결용입니다

---

## 2. 로컬 환경 설정

### 옵션 1: .env.production 파일 생성 (권장)

프로젝트 루트에 `.env.production` 파일을 만들고 다음 내용을 입력:

```env
# Render 프로덕션 DB 연결 설정
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=.render.com,localhost,127.0.0.1

# Render External Database URL (위에서 복사한 URL)
DATABASE_URL=postgresql://finance_user:abc123XYZ456@dpg-xxxxx.oregon-postgres.render.com:5432/finance_db
```

**SECRET_KEY는 Render Environment Variables의 값과 동일하게 설정하세요.**

### 옵션 2: 명령어에서 직접 전달 (Windows)

환경 변수를 일시적으로 설정:

```cmd
set DATABASE_URL=postgresql://finance_user:abc123XYZ456@dpg-xxxxx.oregon-postgres.render.com:5432/finance_db
```

---

## 3. 데이터 수집 실행

### 전체 프로세스 (처음 배포 시)

프로젝트 디렉토리에서 다음 명령어를 **순서대로** 실행:

#### 1단계: 한국 주식 기업 정보 수집

```bash
python manage.py kr_step01_get_companyinfo
```

**예상 결과:**
- KOSPI, KOSDAQ, KONEX 기업 정보 수집
- 약 2,877개 기업 데이터베이스에 저장

#### 2단계: 한국 주식 가격 데이터 수집 (3년치)

```bash
python manage.py kr_step02_get_past_price
```

**예상 결과:**
- 3년치 (1,095일) 가격 데이터 수집
- 약 1,020,000건 데이터 저장
- 소요 시간: 약 30분 ~ 1시간

#### 3단계: 미국 주식 기업 정보 생성

```bash
python manage.py create_us_basic
```

**예상 결과:**
- 7개 주요 미국 주식 기본 정보 생성 (AAPL, GOOGL, MSFT, TSLA, NVDA, AMZN, META)
- API 호출 없이 즉시 생성

#### 4단계: 미국 주식 가격 데이터 수집 (2024년부터)

```bash
python manage.py us_step02_get_past_price --start 2024-01-01
```

**예상 결과:**
- 2024-01-01부터 현재까지 가격 데이터 수집
- 약 461건 × 7개 = 3,227건 데이터 저장
- 소요 시간: 약 5~10분

### 빠른 테스트용 (일부 종목만)

```bash
# 한국 주요 5개 종목만
python manage.py kr_step01_get_companyinfo --codes 005930,000660,035420,051910,035720
python manage.py kr_step02_get_past_price --codes 005930,000660,035420,051910,035720

# 미국 주식 (기본 7개)
python manage.py create_us_basic
python manage.py us_step02_get_past_price --start 2024-01-01
```

---

## 4. 데이터 확인

### Django Shell로 데이터 확인

```bash
python manage.py shell
```

```python
from stocks.models import CompanyInfo, PriceData, USCompanyInfo, USPriceData

# 데이터 개수 확인
print(f"한국 기업: {CompanyInfo.objects.count()}개")
print(f"한국 가격 데이터: {PriceData.objects.count()}건")
print(f"미국 기업: {USCompanyInfo.objects.count()}개")
print(f"미국 가격 데이터: {USPriceData.objects.count()}건")

# 미국 종목 목록 확인
for company in USCompanyInfo.objects.all():
    print(f"{company.symbol}: {company.company_name}")

# 특정 종목 가격 데이터 확인
apple_prices = USPriceData.objects.filter(company__symbol='AAPL').count()
print(f"AAPL 가격 데이터: {apple_prices}건")
```

### 한 줄 명령어로 확인

```bash
python manage.py shell -c "from stocks.models import CompanyInfo, PriceData, USCompanyInfo, USPriceData; print(f'한국: {CompanyInfo.objects.count()}개 기업, {PriceData.objects.count()}건 가격'); print(f'미국: {USCompanyInfo.objects.count()}개 기업, {USPriceData.objects.count()}건 가격')"
```

---

## 5. 일일 자동 업데이트 설정

데이터 수집 완료 후, **Render Cron Job**을 설정하여 매일 자동으로 최신 데이터를 업데이트합니다.

### Cron Job 생성

1. **Render Dashboard** → **Cron Jobs** → **New Cron Job**

2. **설정:**
   - **Name**: `Daily Stock Data Update`
   - **Environment**: 프로젝트와 동일한 환경 선택
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python manage.py daily_update`
   - **Schedule**: `0 1 * * *` (매일 오전 1시 UTC = 한국시간 오전 10시)

3. **Environment Variables** (프로젝트와 동일하게 설정):
   - `SECRET_KEY`: (프로젝트와 동일)
   - `DATABASE_URL`: (자동 연결됨)
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.render.com`

### Cron Job 동작 확인

- Render Dashboard에서 Cron Job 로그 확인
- 최초 실행 후 데이터베이스에서 새로운 가격 데이터 확인

---

## 6. 문제 해결

### Q1: "psycopg2.OperationalError: SSL connection" 에러

**원인:** SSL 연결 설정 문제

**해결:**
```bash
# DATABASE_URL 끝에 ?sslmode=require 추가
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### Q2: "password authentication failed" 에러

**원인:** 잘못된 External Database URL 또는 만료된 비밀번호

**해결:**
1. Render Dashboard에서 최신 External Database URL 다시 복사
2. `.env.production` 파일 업데이트
3. 명령어 재실행

### Q3: Yahoo Finance "429 Too Many Requests" 에러

**원인:** API Rate Limit 초과

**해결:**
```bash
# 대기 시간 늘리기 (기본 0.5초 → 2초)
python manage.py us_step02_get_past_price --start 2024-01-01 --batch-delay 2.0

# 또는 나중에 다시 시도
```

### Q4: "No module named 'psycopg'" 에러

**원인:** psycopg 패키지 설치 안 됨

**해결:**
```bash
pip install psycopg[binary]
```

### Q5: 한국 데이터는 성공했는데 미국 데이터가 안 들어감

**원인:** Yahoo Finance API 차단

**해결:**
1. 잠시 대기 후 재시도 (15~30분)
2. VPN 사용
3. `--batch-delay` 값 증가
4. 다음 날 Cron Job이 자동으로 재시도

---

## 📊 예상 데이터베이스 용량

### 전체 데이터 (3년치)

| 항목 | 개수 | 용량 |
|-----|-----|-----|
| 한국 기업 | 2,877개 | ~1 MB |
| 한국 가격 데이터 | ~1,020,000건 | ~400 MB |
| 미국 기업 | 7개 | ~1 KB |
| 미국 가격 데이터 | ~3,227건 | ~200 KB |
| **총합** | | **~410 MB** |

✅ **Render 무료 티어 1GB 제한 내에서 안전**

---

## 🎯 완료 체크리스트

- [ ] Render External Database URL 복사
- [ ] `.env.production` 파일 생성 및 설정
- [ ] 한국 기업 정보 수집 완료
- [ ] 한국 가격 데이터 수집 완료 (~2,877개 기업)
- [ ] 미국 기업 정보 생성 완료 (7개)
- [ ] 미국 가격 데이터 수집 완료 (7개)
- [ ] 데이터베이스 확인 (Django shell)
- [ ] Render Cron Job 설정 완료
- [ ] Cron Job 첫 실행 확인

---

## 📞 추가 도움

- **Render 문서**: https://docs.render.com/databases
- **Django 문서**: https://docs.djangoproject.com/
- **프로젝트 문서**: `RENDER_DEPLOY.md`, `DATA_COLLECTION_GUIDE.md`

---

✅ 이제 로컬에서 프로덕션 DB에 안전하게 데이터를 수집할 수 있습니다!

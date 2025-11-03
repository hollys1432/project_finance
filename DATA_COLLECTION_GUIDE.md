# 데이터 수집 가이드

이 문서는 주식 데이터 수집을 위한 명령어 사용법을 설명합니다.

## ⚙️ 기본 설정

**기본 수집 기간: 3년 (1,095일)**
- 명령어를 옵션 없이 실행하면 최근 3년치 데이터를 수집합니다
- 데이터베이스 용량을 최적화하기 위해 3년으로 설정되었습니다

## 📊 예상 데이터베이스 용량 (3년 기준)

| 수집 범위 | 예상 용량 |
|-----------|-----------|
| 한국 전체 (KOSPI/KOSDAQ/KONEX) | ~490 MB |
| 미국 주요 종목 (S&P500 + NASDAQ100) | ~48 MB |
| **한국 + 미국 주요 종목 합계** | **~700 MB** |
| NYSE 전체 포함 시 | ~1 GB |

---

## 🇰🇷 한국 주식 데이터 수집

### Step 1: 기업 정보 수집
```bash
python manage.py kr_step01_get_companyinfo
```

**수집 내용:**
- KOSPI, KOSDAQ, KONEX 전체 상장사 정보
- 약 2,450개 종목
- 용량: ~0.4 MB

**옵션:**
```bash
# 특정 종목만 수집
python manage.py kr_step01_get_companyinfo --filter "삼성"

# Dry-run (실제 저장 없이 확인만)
python manage.py kr_step01_get_companyinfo --dry-run

# 기존 데이터 업데이트
python manage.py kr_step01_get_companyinfo --update
```

---

### Step 2: 가격 데이터 수집

**기본 사용 (전체 종목, 3년치):**
```bash
python manage.py kr_step02_get_past_price
```
- 예상 용량: ~490 MB
- 소요 시간: 약 1~2시간 (API 호출 제한으로 시간 소요)

**특정 종목만 수집:**
```bash
# 삼성전자, SK하이닉스, NAVER만
python manage.py kr_step02_get_past_price --codes "005930,000660,035420"
```

**시장별 수집:**
```bash
# KOSPI만
python manage.py kr_step02_get_past_price --markets "KOSPI"

# KOSDAQ만
python manage.py kr_step02_get_past_price --markets "KOSDAQ"

# 여러 시장
python manage.py kr_step02_get_past_price --markets "KOSPI,KOSDAQ"
```

**기간 지정:**
```bash
# 5년치 데이터
python manage.py kr_step02_get_past_price --start 2020-01-01

# 1년치 데이터만
python manage.py kr_step02_get_past_price --start 2024-01-01

# 특정 기간
python manage.py kr_step02_get_past_price --start 2023-01-01 --end 2023-12-31
```

**증분 업데이트 (일일 업데이트용):**
```bash
# 마지막 저장일 이후 데이터만 수집
python manage.py kr_step02_get_past_price --only-latest
```

---

## 🇺🇸 미국 주식 데이터 수집

### Step 1: 기업 정보 수집

**기본 (S&P500 + NASDAQ100):**
```bash
python manage.py us_step01_get_company_info
```
- 약 550개 종목
- 용량: ~0.15 MB

**S&P 500만:**
```bash
python manage.py us_step01_get_company_info --sp500
```

**NASDAQ 100만:**
```bash
python manage.py us_step01_get_company_info --nasdaq100
```

**NYSE 전체 (⚠️ 대용량):**
```bash
python manage.py us_step01_get_company_info --nyse
```
- 약 3,500개 종목
- 가격 데이터 포함 시 ~1 GB

**특정 종목만:**
```bash
python manage.py us_step01_get_company_info --symbols "AAPL,GOOGL,MSFT,TSLA"
```

---

### Step 2: 가격 데이터 수집

**기본 사용 (3년치):**
```bash
python manage.py us_step02_get_past_price
```
- 예상 용량: ~48 MB (주요 종목 550개)
- 소요 시간: 약 30분~1시간

**특정 종목만:**
```bash
python manage.py us_step02_get_past_price --symbols "AAPL,GOOGL,MSFT"
```

**조정 종가 사용:**
```bash
# 배당/분할 자동 조정된 가격 저장
python manage.py us_step02_get_past_price --auto-adjust
```

**기간 지정:**
```bash
# 5년치
python manage.py us_step02_get_past_price --start 2020-01-01

# 1년치
python manage.py us_step02_get_past_price --start 2024-01-01
```

---

### Step 3: 일일 업데이트 (자동화 추천)

```bash
python manage.py us_step03_daily_update
```
- 마지막 저장일 이후 데이터만 증분 수집
- Cron 또는 스케줄러로 매일 자동 실행 권장

---

## 💾 Render 배포 시 권장 사항

### 무료 플랜 (1GB 제한)
```bash
# 한국: 주요 종목만 (예: 시가총액 상위)
python manage.py kr_step01_get_companyinfo
python manage.py kr_step02_get_past_price --markets "KOSPI" --codes "005930,000660,035420,..."

# 미국: 주요 종목만
python manage.py us_step01_get_company_info --symbols "AAPL,GOOGL,MSFT,TSLA,NVDA"
python manage.py us_step02_get_past_price --symbols "AAPL,GOOGL,MSFT,TSLA,NVDA"
```
**예상 용량: ~100-200 MB**

### 유료 플랜 ($7/월, 10GB)
```bash
# 한국 전체 + 미국 주요 종목
python manage.py kr_step01_get_companyinfo
python manage.py kr_step02_get_past_price

python manage.py us_step01_get_company_info
python manage.py us_step02_get_past_price
```
**예상 용량: ~700 MB**

---

## 🔧 유용한 옵션들

### 공통 옵션
```bash
--batch-size 1000          # 배치 삽입 크기 (기본: 1000)
--sleep-min 0.5            # API 호출 간 최소 대기 시간 (초)
--sleep-max 1.5            # API 호출 간 최대 대기 시간 (초)
--dry-run                  # 실제 저장 없이 시뮬레이션만
--retry 3                  # API 실패 시 재시도 횟수
```

### 예제
```bash
# 빠른 수집 (API 대기 시간 단축, 차단 위험 있음)
python manage.py kr_step02_get_past_price --sleep-min 0.1 --sleep-max 0.3

# 안전한 수집 (API 호출 간격 길게)
python manage.py us_step02_get_past_price --sleep-min 1.0 --sleep-max 2.0

# 재시도 많이
python manage.py kr_step02_get_past_price --retry 5
```

---

## 🗄️ 데이터베이스 관리

### 현재 용량 확인
```bash
python manage.py dbshell
```
```sql
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC;
```

### 오래된 데이터 삭제
```python
# Django shell에서
python manage.py shell
```
```python
from datetime import date, timedelta
from stocks.models import PriceData, USPriceData

# 3년 이전 데이터 삭제
cutoff = date.today() - timedelta(days=3*365)
PriceData.objects.filter(date__lt=cutoff).delete()
USPriceData.objects.filter(date__lt=cutoff).delete()
```

### 데이터베이스 최적화
```bash
python manage.py dbshell
```
```sql
VACUUM FULL price_data;
VACUUM FULL us_price_data;
ANALYZE;
```

---

## ⏰ 자동화 (Cron 설정)

매일 오후 6시에 자동 업데이트:
```bash
crontab -e
```
```
0 18 * * * cd /path/to/project && python manage.py kr_step02_get_past_price --only-latest
5 18 * * * cd /path/to/project && python manage.py us_step03_daily_update
```

---

## 🚨 문제 해결

### API 호출 차단 시
- `--sleep-min`, `--sleep-max` 값을 크게 설정
- `--retry` 값을 늘림
- 특정 시간대를 피해서 실행

### 용량 초과 시
- 특정 종목만 선택하여 수집
- 수집 기간을 1년 또는 2년으로 단축
- 오래된 데이터 삭제

### 명령어 실행 시간이 너무 길 때
- `--codes` 또는 `--symbols`로 종목 수 제한
- `--markets` 옵션으로 시장 제한
- 병렬 처리는 지원하지 않으므로 여러 터미널에서 나눠서 실행 가능

---

## 📝 추가 정보

- 모든 명령어는 재실행 시 중복 데이터를 자동으로 건너뜁니다
- `unique_together` 제약조건으로 중복 방지
- 증분 수집이 기본 동작이므로 안전하게 재실행 가능

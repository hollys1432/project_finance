# 주식 데이터 수집 및 퀀트 백테스팅 시스템

Django 기반의 주식 데이터 수집 및 퀀트 전략 백테스팅 플랫폼입니다.

## 🌟 주요 기능

- **한국 주식 데이터 수집** (KOSPI, KOSDAQ, KONEX)
- **미국 주식 데이터 수집** (S&P500, NASDAQ100, NYSE)
- **퀀트 전략 백테스팅**
- **자동 데이터 업데이트**
- **Render 배포 지원**

---

## 📁 프로젝트 구조

```
v28_deploy/
├── config/              # Django 설정
│   ├── settings.py      # 데이터베이스 설정, 환경 변수 관리
│   └── urls.py
│
├── stocks/              # 주식 데이터 앱
│   ├── models.py        # CompanyInfo, PriceData, USCompanyInfo, USPriceData
│   ├── views.py
│   └── management/commands/
│       ├── kr_step01_get_companyinfo.py    # 한국 기업 정보 수집
│       ├── kr_step02_get_past_price.py     # 한국 주가 데이터 수집
│       ├── us_step01_get_company_info.py   # 미국 기업 정보 수집
│       ├── us_step02_get_past_price.py     # 미국 주가 데이터 수집
│       ├── us_step03_daily_update.py       # 미국 일일 업데이트
│       ├── init_data.py                    # 초기 데이터 로딩 (자동화)
│       └── daily_update.py                 # 일일 자동 업데이트 (Cron Job용)
│
├── quant/               # 퀀트 전략 앱
│   ├── models.py        # Strategy, Backtest, Signal
│   └── management/commands/
│       ├── run_backtest.py
│       └── run_backtest_all.py
│
├── static/              # 정적 파일
├── staticfiles/         # 수집된 정적 파일 (배포용)
│
├── build.sh             # Render 빌드 스크립트
├── requirements.txt     # Python 패키지
├── .env.example         # 환경 변수 템플릿
├── .env                 # 로컬 개발용 환경 변수
└── .gitignore
```

---

## 🚀 로컬 개발 환경 설정

### 1. 저장소 클론 및 가상환경 생성

```bash
git clone <repository-url>
cd v28_deploy

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일 생성 (`.env.example` 참고):
```bash
cp .env.example .env
```

`.env` 파일 편집:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=finance
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
```

### 4. PostgreSQL 설정

1. PostgreSQL 설치 및 실행
2. 데이터베이스 생성:
```sql
CREATE DATABASE finance;
```

### 5. 마이그레이션

```bash
python manage.py migrate
```

### 6. 개발 서버 실행

```bash
python manage.py runserver
```

http://localhost:8000 에서 확인

---

## 📊 데이터 수집

### 빠른 시작 (주요 종목만)

```bash
python manage.py init_data --quick
```
- 한국 주요 5개 종목, 미국 주요 7개 종목
- 1년치 데이터
- 약 10~20 MB, 5~10분 소요

### 전체 데이터 수집

**한국 주식:**
```bash
# 1. 기업 정보 수집
python manage.py kr_step01_get_companyinfo

# 2. 가격 데이터 수집 (3년치)
python manage.py kr_step02_get_past_price
```

**미국 주식:**
```bash
# 1. 기업 정보 수집
python manage.py us_step01_get_company_info

# 2. 가격 데이터 수집 (3년치)
python manage.py us_step02_get_past_price
```

**자세한 사용법은 `DATA_COLLECTION_GUIDE.md` 참고**

---

## 🌐 Render 배포

### 배포 절차

1. **GitHub에 코드 푸시**
2. **Render에서 PostgreSQL 생성**
3. **Web Service 생성**
   - Build Command: `./build.sh`
   - Start Command: `gunicorn config.wsgi:application`
4. **환경 변수 설정**
5. **배포 완료 후 Render Shell에서 초기 데이터 로딩**
   ```bash
   python manage.py init_data --quick
   ```
6. **Cron Job 설정 (일일 자동 업데이트)**
   - Command: `python manage.py daily_update`
   - Schedule: `0 18 * * *` (매일 오후 6시 UTC)

**자세한 배포 가이드: `RENDER_DEPLOY.md`**
**자동화 설정 가이드: `RENDER_AUTOMATION.md`**

---

## 📖 문서

- **`RENDER_DEPLOY.md`** - Render 배포 단계별 가이드
- **`RENDER_AUTOMATION.md`** - 자동 데이터 수집 설정 가이드
- **`DATA_COLLECTION_GUIDE.md`** - 데이터 수집 명령어 상세 사용법

---

## 🎯 주요 명령어

### 초기 설정

```bash
# 데이터베이스 마이그레이션
python manage.py migrate

# 정적 파일 수집 (배포용)
python manage.py collectstatic

# Superuser 생성
python manage.py createsuperuser
```

### 데이터 수집

```bash
# 초기 데이터 로딩 (빠른 모드)
python manage.py init_data --quick

# 전체 초기화
python manage.py init_data

# 일일 업데이트 (증분 수집)
python manage.py daily_update

# 한국 주식만
python manage.py kr_step02_get_past_price --only-latest

# 미국 주식만
python manage.py us_step03_daily_update
```

### 백테스팅

```bash
# 특정 종목 백테스트
python manage.py run_backtest --stock 005930 --strategy ma_cross

# 전체 종목 백테스트
python manage.py run_backtest_all --market kr

# 백테스트 결과 확인
python manage.py show_backtest_results
```

---

## 💾 데이터베이스 용량 (3년 기준)

| 수집 범위 | 예상 용량 |
|-----------|-----------|
| 빠른 초기화 (주요 종목, 1년) | ~20 MB |
| 한국 KOSPI (3년) | ~200 MB |
| 한국 전체 (3년) | ~490 MB |
| 미국 주요 (S&P500+NASDAQ100, 3년) | ~48 MB |
| **한국 + 미국 전체 (3년)** | **~700 MB** |

---

## 🛠️ 기술 스택

- **Backend:** Django 5.2.1
- **Database:** PostgreSQL
- **데이터 소스:**
  - 한국: pykrx
  - 미국: yfinance
- **배포:** Render
- **웹서버:** Gunicorn
- **정적 파일:** WhiteNoise

---

## 📝 환경 변수

### 필수 환경 변수

```env
SECRET_KEY=<your-secret-key>
DEBUG=False
ALLOWED_HOSTS=.render.com,localhost
DATABASE_URL=<postgresql-url>
```

### 선택적 환경 변수

```env
# 초기 데이터 자동 로딩 (권장하지 않음)
INIT_DATA=false
INIT_MODE=quick
```

---

## 🔧 개발

### 테스트

```bash
python manage.py test
```

### 코드 체크

```bash
python manage.py check
```

### 데이터베이스 셸

```bash
python manage.py dbshell
```

---

## 📊 모델 구조

### stocks.models

- **CompanyInfo** - 한국 기업 정보
- **PriceData** - 한국 주가 데이터
- **USCompanyInfo** - 미국 기업 정보
- **USPriceData** - 미국 주가 데이터
- **MarketIndex** - 시장 지수
- **WatchList** - 관심 종목

### quant.models

- **Strategy** - 퀀트 전략
- **Backtest** - 백테스트 결과
- **Signal** - 거래 신호

---

## 🤝 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이선스

This project is licensed under the MIT License.

---

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

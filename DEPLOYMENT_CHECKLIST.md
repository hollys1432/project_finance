# 🚀 배포 체크리스트

Render에 배포하기 전 마지막 확인 사항입니다.

---

## ✅ 배포 전 체크리스트

### 1. 코드 준비 상태

- [x] **requirements.txt** - 모든 필요한 패키지 포함됨
  - Django, psycopg2-binary, gunicorn, whitenoise ✅
  - python-decouple, dj-database-url ✅
  - yfinance, pykrx (데이터 수집용) ✅
  - pandas, numpy, lxml ✅

- [x] **settings.py** - 프로덕션 설정 완료
  - 환경 변수로 SECRET_KEY, DEBUG, ALLOWED_HOSTS 관리 ✅
  - 데이터베이스 환경 변수 설정 ✅
  - WhiteNoise 미들웨어 추가 ✅
  - 보안 설정 (HTTPS, HSTS, Secure Cookie) ✅

- [x] **build.sh** - Render 빌드 스크립트 작성됨
  - 의존성 설치 ✅
  - collectstatic ✅
  - migrate ✅
  - 선택적 초기 데이터 로딩 (환경 변수로 제어) ✅

- [x] **.env.example** - 환경 변수 템플릿 작성됨 ✅

- [x] **.gitignore** - 민감한 파일 제외 설정
  - .env 파일 ✅
  - __pycache__ ✅
  - *.log ✅
  - db.sqlite3 ✅

- [x] **자동화 명령어** 작성 완료
  - init_data.py (초기 데이터 로딩) ✅
  - daily_update.py (일일 업데이트) ✅

---

## 📝 배포 단계

### Step 1: GitHub에 코드 푸시

```bash
# .env 파일이 gitignore에 포함되어 있는지 확인
git status

# 커밋 및 푸시
git add .
git commit -m "Render 배포 준비 완료"
git push origin main
```

**⚠️ 중요:** `.env` 파일이 커밋되지 않았는지 반드시 확인!

---

### Step 2: Render PostgreSQL 생성

1. [Render Dashboard](https://dashboard.render.com) 접속
2. "New +" → "PostgreSQL" 선택
3. 설정:
   - **Name:** `finance-db` (원하는 이름)
   - **Database:** `finance`
   - **User:** 자동 생성
   - **Region:** Singapore 또는 가까운 지역
   - **PostgreSQL Version:** 16
   - **Plan:** Free (또는 원하는 플랜)
4. "Create Database" 클릭
5. **Internal Database URL** 복사 (나중에 사용)

---

### Step 3: Render Web Service 생성

1. "New +" → "Web Service" 선택
2. GitHub 저장소 연결
3. 설정:
   - **Name:** `finance-app` (원하는 이름)
   - **Region:** PostgreSQL과 **같은 지역** 선택 ⚠️
   - **Branch:** `main`
   - **Root Directory:** (비워두기)
   - **Runtime:** `Python 3`
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn config.wsgi:application`
   - **Plan:** Free (또는 원하는 플랜)

---

### Step 4: 환경 변수 설정

Web Service의 **Environment** 탭에서 다음 환경 변수 추가:

#### 필수 환경 변수

```env
SECRET_KEY=<Django secret key - 50자 이상 랜덤 문자열>
DEBUG=False
ALLOWED_HOSTS=.render.com
DATABASE_URL=<Step 2에서 복사한 Internal Database URL>
```

**SECRET_KEY 생성 방법:**
```python
# 로컬에서 실행
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

#### 초기 데이터 자동 로딩 (무료 플랜 권장 ⭐)

⚠️ **무료 플랜은 Shell이 없으므로 이 방법을 사용하세요!**

```env
INIT_DATA=true
INIT_MODE=quick
```

**INIT_MODE 옵션:**
- `quick` - 주요 종목, 1년치 (~20MB, 5~10분) ⭐ 권장
- `kr-only` - 한국만 (~490MB, 타임아웃 위험)
- `us-only` - 미국만 (~48MB)
- `full` - 전체 (~700MB, 타임아웃 위험 높음)

---

### Step 5: 배포 시작

1. "Create Web Service" 클릭
2. 빌드 시작 (약 5~10분 소요)
3. **Logs** 탭에서 진행 상황 확인
4. 배포 완료 확인

**예상 빌드 로그:**
```
==> Installing dependencies...
==> Collecting static files...
==> Running migrations...
==> Build 완료!
```

---

### Step 6: 초기 데이터 로딩 확인

#### 무료 플랜 사용자

**Step 4에서 환경 변수를 설정했다면:**
- 빌드 완료 후 자동으로 데이터 수집 시작
- **Logs** 탭에서 진행 상황 확인:
  ```
  초기 데이터 로딩 시작...
  [1/4] 한국 기업 정보 수집 중...
  ✓ 한국 기업 정보 수집 완료
  ...
  ```

**환경 변수를 설정하지 않았다면:**
1. 로컬에서 프로덕션 DB에 연결 (자세한 방법은 `LOCAL_TO_PRODUCTION.md` 참고)
2. 또는 유료 플랜으로 업그레이드

#### 유료 플랜 사용자

**Shell** 탭에서 직접 실행:

```bash
# 빠른 초기화
python manage.py init_data --quick

# 또는 커스텀 옵션
python manage.py init_data --kr-markets "KOSPI" --skip-us
python manage.py init_data --skip-kr --us-symbols "AAPL,GOOGL,MSFT"
```

---

### Step 7: Cron Job 설정 (일일 자동 업데이트)

1. Render Dashboard → "New +" → "Cron Job"
2. 설정:
   - **Name:** `daily-stock-update`
   - **Region:** Web Service와 같은 지역
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Command:** `python manage.py daily_update`
   - **Schedule:** `0 18 * * *` (매일 오후 6시 UTC)

3. **Environment** 탭에서 Web Service와 동일한 환경 변수 연결
4. "Create Cron Job" 클릭

---

### Step 8: Superuser 생성 (선택)

Admin 페이지 사용을 위해:

```bash
# Shell에서 실행
python manage.py createsuperuser
```

---

## ✅ 배포 후 확인사항

### 1. 사이트 접속 확인
- Render에서 제공한 URL 접속
- 페이지가 정상적으로 로드되는지 확인

### 2. Admin 페이지 확인
- `https://your-app.onrender.com/admin/` 접속
- 로그인 가능한지 확인

### 3. 데이터베이스 확인
```bash
# Shell에서 실행
python manage.py shell
```
```python
from stocks.models import CompanyInfo, USCompanyInfo
print(f"한국 기업: {CompanyInfo.objects.count()}개")
print(f"미국 기업: {USCompanyInfo.objects.count()}개")
```

### 4. Cron Job 로그 확인
- Cron Job의 **Logs** 탭에서 실행 로그 확인
- 다음 실행 예정 시각 확인

---

## 🚨 문제 발생 시

### 빌드 실패
- **Logs** 탭에서 에러 메시지 확인
- 대부분 환경 변수 설정 문제
- DATABASE_URL이 올바른지 확인

### 500 에러
1. Logs 확인
2. 일시적으로 `DEBUG=True`로 설정 (에러 확인 후 즉시 False로!)
3. collectstatic이 정상 실행되었는지 확인

### 정적 파일 로드 안됨
- WhiteNoise 설정 확인
- `python manage.py collectstatic --no-input` 재실행

### 데이터베이스 연결 오류
- DATABASE_URL 형식 확인
- PostgreSQL과 Web Service가 같은 Region인지 확인
- Internal Database URL을 사용했는지 확인 (External URL 아님)

---

## 📊 배포 후 용량 체크

### 데이터베이스 용량 확인
```bash
# Shell에서 실행
python manage.py dbshell
```
```sql
SELECT
    pg_size_pretty(pg_database_size('finance')) AS db_size;
```

### 무료 플랜 제한
- PostgreSQL: 1 GB
- 90일 후 자동 삭제

---

## 🎯 배포 완료!

축하합니다! 이제 다음을 할 수 있습니다:

1. **자동 데이터 수집** - 매일 자동으로 최신 데이터 업데이트
2. **퀀트 백테스팅** - 수집된 데이터로 전략 테스트
3. **API 엔드포인트** - REST API로 데이터 제공
4. **커스텀 도메인** - 원하는 도메인 연결 가능

---

## 📚 추가 문서

- **RENDER_DEPLOY.md** - 상세 배포 가이드
- **RENDER_AUTOMATION.md** - 자동화 설정 가이드
- **DATA_COLLECTION_GUIDE.md** - 데이터 수집 가이드
- **README.md** - 프로젝트 개요

---

## 💡 팁

1. **무료 플랜 최적화**
   - 주요 종목만 선택 수집
   - 1~2년치 데이터만 유지
   - 정기적으로 오래된 데이터 정리

2. **모니터링**
   - Render Logs 정기적으로 확인
   - Cron Job 실행 여부 확인
   - 데이터베이스 용량 모니터링

3. **백업**
   - 중요한 데이터는 별도 백업
   - 무료 플랜은 90일 후 삭제됨

---

**배포에 성공했다면 이 체크리스트는 저장해두세요!** 🎉

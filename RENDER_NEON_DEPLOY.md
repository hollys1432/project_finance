# Render + Neon 배포 가이드

Django 주식 분석 앱을 Render (웹 서버) + Neon (PostgreSQL DB) 조합으로 배포하는 가이드입니다.

## 📋 목차
1. [Neon PostgreSQL 설정](#1-neon-postgresql-설정)
2. [Render 웹 서비스 배포](#2-render-웹-서비스-배포)
3. [로컬에서 프로덕션 DB 연결하여 데이터 수집](#3-로컬에서-프로덕션-db-연결하여-데이터-수집)
4. [배포 확인](#4-배포-확인)
5. [문제 해결](#5-문제-해결)

---

## 1. Neon PostgreSQL 설정

### 1.1 Neon 프로젝트 생성

1. **Neon 콘솔 접속**: https://console.neon.tech
2. **Sign Up / Login** (GitHub 계정으로 간편 가입 가능)
3. **New Project** 클릭
4. **프로젝트 설정**:
   - **Project name**: `finance-app` (원하는 이름)
   - **Region**: `AWS Singapore (ap-southeast-1)` ← 한국과 가장 가까운 지역
   - **Database name**: `finance`
   - **PostgreSQL Version**: 16 (기본값)
5. **Create Project** 클릭

### 1.2 Connection String 복사

프로젝트 생성 후 Dashboard에서 **Connection String**을 복사합니다:

```
postgresql://[user]:[password]@[host]/[database]?sslmode=require
```

예시:
```
postgresql://finance_user:abc123xyz@ep-cool-sound-12345.ap-southeast-1.aws.neon.tech/finance?sslmode=require
```

> ⚠️ **중요**: 이 Connection String은 안전하게 보관하세요!

### 1.3 Neon 무료 티어 제한사항

- **Storage**: 500 MB (주가 데이터 2년치 가능)
- **Compute**: 191.9 시간/월
- **Auto-suspend**: 5분 동안 비활성 시 자동 중지

---

## 2. Render 웹 서비스 배포

### 2.1 GitHub 저장소 준비

1. **GitHub에 코드 푸시**:
   ```bash
   git add .
   git commit -m "Render + Neon 배포 설정 완료"
   git push origin main
   ```

2. **필수 파일 확인**:
   - ✅ `render.yaml` - Render 배포 설정
   - ✅ `build.sh` - 빌드 스크립트
   - ✅ `requirements.txt` - Python 패키지
   - ✅ `runtime.txt` - Python 버전

### 2.2 Render에서 서비스 생성

1. **Render 대시보드**: https://dashboard.render.com
2. **New** → **Blueprint** 클릭
3. **GitHub 저장소 연결**:
   - GitHub 계정 연결
   - 저장소 선택 (`v30_deploy` 또는 해당 저장소)
   - Branch: `main`
4. **Blueprint 감지 확인**:
   - `render.yaml` 파일을 자동으로 감지합니다
5. **Apply** 클릭

### 2.3 환경변수 설정

Render Dashboard에서 생성된 Web Service로 이동 후 **Environment** 탭에서 설정:

| Key | Value | 설명 |
|-----|-------|------|
| `SECRET_KEY` | (자동 생성됨) | Django 시크릿 키 |
| `DEBUG` | `False` | 프로덕션 모드 |
| `ALLOWED_HOSTS` | `.render.com` | Render 호스트 허용 |
| `DATABASE_URL` | `postgresql://...` | **Neon Connection String 붙여넣기** |

> 💡 **DATABASE_URL**: Neon에서 복사한 Connection String을 그대로 붙여넣으세요.

### 2.4 배포 시작

- **Save Changes** → 자동으로 빌드 시작
- **Logs** 탭에서 빌드 진행 상황 확인
- 성공 시 `Build 완료!` 메시지 표시

---

## 3. 로컬에서 프로덕션 DB 연결하여 데이터 수집

Render의 무료 티어는 compute 시간 제한이 있으므로, **로컬 환경에서 Neon DB에 연결하여 데이터를 수집**합니다.

### 3.1 로컬 환경변수 설정

프로젝트 루트에 `.env` 파일 생성 또는 수정:

```bash
# .env
DATABASE_URL=postgresql://[user]:[password]@[host]/[database]?sslmode=require
DEBUG=False
SECRET_KEY=your-local-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

> ⚠️ **DATABASE_URL**: Neon Connection String 사용!

### 3.2 마이그레이션 확인

```bash
python manage.py migrate
```

### 3.3 데이터 수집 (500MB 제한 고려)

#### 옵션 1: 2년 데이터 (권장) - 약 350MB

```bash
# 한국 주식 기본 정보
python manage.py kr_step01_get_companyinfo

# 한국 주가 데이터 (최근 2년)
python manage.py kr_step02_get_past_price --start 2023-12-01

# 미국 주식 기본 정보
python manage.py create_us_basic

# 미국 주가 데이터 (최근 2년)
python manage.py us_step02_get_past_price --start 2023-12-01
```

#### 옵션 2: 1년 데이터 (안전) - 약 192MB

```bash
# 한국 주식 기본 정보
python manage.py kr_step01_get_companyinfo

# 한국 주가 데이터 (최근 1년)
python manage.py kr_step02_get_past_price --start 2024-12-01

# 미국 주식 기본 정보
python manage.py create_us_basic

# 미국 주가 데이터 (최근 1년)
python manage.py us_step02_get_past_price --start 2024-12-01
```

#### 옵션 3: 하이브리드 (한국 2년 + 미국 1년) - 약 230MB

```bash
# 한국: 2년
python manage.py kr_step01_get_companyinfo
python manage.py kr_step02_get_past_price --start 2023-12-01

# 미국: 1년
python manage.py create_us_basic
python manage.py us_step02_get_past_price --start 2024-12-01
```

### 3.4 데이터 수집 소요 시간

- **한국 주가 2년**: 약 30-60분
- **미국 주가 2년**: 약 2-4시간 (종목 수에 따라)
- **API Rate Limit**: 자동으로 재시도 처리됨

### 3.5 데이터베이스 크기 확인 (Neon Dashboard)

Neon Console → 프로젝트 → **Storage** 탭에서 현재 사용량 확인 가능

---

## 4. 배포 확인

### 4.1 웹사이트 접속

Render Dashboard에서 제공되는 URL로 접속:
```
https://finance-app-xxxxx.onrender.com
```

### 4.2 동작 확인

1. **메인 페이지 로드 확인**
2. **한국 주식 리스트** 확인
3. **미국 주식 리스트** 확인
4. **특정 종목 상세 페이지** 확인

### 4.3 로그 확인

Render Dashboard → **Logs** 탭:
- 에러 메시지 확인
- 성능 모니터링

---

## 5. 문제 해결

### 5.1 빌드 실패

**증상**: `build.sh` 실행 중 오류

**해결**:
```bash
# 로컬에서 빌드 테스트
chmod +x build.sh
./build.sh
```

### 5.2 데이터베이스 연결 실패

**증상**: `could not connect to server`

**해결**:
1. Neon Connection String 확인
2. `?sslmode=require` 파라미터 포함 여부 확인
3. Neon Dashboard에서 DB 상태 확인 (Auto-suspend 해제)

### 5.3 Static 파일 404

**증상**: CSS/JS 파일 로드 안 됨

**해결**:
```bash
# 로컬에서 테스트
python manage.py collectstatic --no-input
```

`config/settings.py`에 WhiteNoise 설정 확인:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← 있어야 함
    ...
]
```

### 5.4 500 Internal Server Error

**증상**: 앱 실행 시 500 에러

**해결**:
1. Render Logs 확인
2. `DEBUG=True`로 임시 변경하여 에러 메시지 확인
3. 마이그레이션 상태 확인:
   ```bash
   python manage.py showmigrations
   ```

### 5.5 Neon DB 용량 초과

**증상**: `disk quota exceeded`

**해결**:
1. 오래된 데이터 삭제:
   ```python
   # 3년 이전 데이터 삭제
   from datetime import date, timedelta
   from stocks.models import PriceData, USPriceData

   cutoff = date.today() - timedelta(days=365*3)
   PriceData.objects.filter(date__lt=cutoff).delete()
   USPriceData.objects.filter(date__lt=cutoff).delete()
   ```

2. 또는 Neon Pro 플랜 업그레이드 고려

---

## 6. 추가 최적화

### 6.1 주기적 데이터 업데이트

Render Cron Jobs (유료) 또는 GitHub Actions로 자동화:

```yaml
# .github/workflows/update_data.yml
name: Update Stock Data
on:
  schedule:
    - cron: '0 0 * * 1'  # 매주 월요일 00:00 UTC
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python manage.py kr_step02_get_past_price --start 7
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### 6.2 캐싱 활용

Redis 대신 로컬 메모리 캐시 사용 (이미 설정됨):

```python
# config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,  # 5분
    }
}
```

---

## 7. 비용 정리

| 서비스 | 무료 티어 | 유료 플랜 |
|--------|-----------|-----------|
| **Render** | 750 시간/월, 0.5 CPU, 512MB RAM | $7/월~ |
| **Neon** | 500MB 스토리지, 191.9 시간/월 compute | $19/월~ |

**총 무료 비용**: $0/월 (제한 내 사용 시)

---

## 8. 체크리스트

배포 전 확인사항:

- [ ] Neon PostgreSQL 프로젝트 생성 완료
- [ ] Neon Connection String 복사
- [ ] GitHub에 코드 푸시 완료
- [ ] Render Blueprint 배포 완료
- [ ] Render 환경변수 설정 (특히 `DATABASE_URL`)
- [ ] 로컬에서 Neon DB 연결 테스트
- [ ] 데이터 수집 완료 (한국/미국 주식)
- [ ] 웹사이트 접속 확인
- [ ] 주요 기능 동작 테스트

---

## 참고 링크

- **Neon 문서**: https://neon.tech/docs
- **Render 문서**: https://render.com/docs
- **Django 배포 가이드**: https://docs.djangoproject.com/en/5.2/howto/deployment/

---

## 문의

배포 중 문제가 발생하면 다음을 확인하세요:
1. Render Logs
2. Neon Database Status
3. GitHub Actions (설정한 경우)

Happy Deploying! 🚀

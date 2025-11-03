# Render 배포 가이드

이 프로젝트를 Render에 배포하기 위한 단계별 가이드입니다.

## 1. Render 계정 준비
1. [Render](https://render.com)에 가입 또는 로그인
2. Dashboard로 이동

## 2. PostgreSQL 데이터베이스 생성
1. Dashboard에서 "New +" → "PostgreSQL" 선택
2. 다음 정보 입력:
   - Name: `finance-db` (원하는 이름)
   - Region: 가까운 지역 선택 (예: Singapore)
   - PostgreSQL Version: 최신 버전
   - Plan: Free 또는 원하는 플랜
3. "Create Database" 클릭
4. 생성 후 "Internal Database URL" 복사 (나중에 사용)

## 3. Web Service 생성
1. Dashboard에서 "New +" → "Web Service" 선택
2. GitHub 저장소 연결 (또는 수동 배포)
3. 다음 정보 입력:
   - Name: `finance-app` (원하는 이름)
   - Region: 데이터베이스와 같은 지역
   - Branch: `main` 또는 배포할 브랜치
   - Runtime: `Python 3`
   - Build Command: `./build.sh`
   - Start Command: `gunicorn config.wsgi:application`

## 4. 환경 변수 설정
Web Service 설정 페이지의 "Environment" 탭에서 다음 환경 변수 추가:

### 필수 환경 변수
```
SECRET_KEY=your-very-secure-random-secret-key-here-make-it-long-and-random
DEBUG=False
ALLOWED_HOSTS=.render.com
DATABASE_URL=<Step 2에서 복사한 Internal Database URL>
```

**SECRET_KEY 생성 방법:**
```python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 초기 데이터 자동 로딩 (무료 플랜 필수 ⭐)

**⚠️ 중요: Render 무료 플랜은 Shell이 없습니다!**

무료 플랜 사용자는 반드시 다음 환경 변수를 추가하세요:
```
INIT_DATA=true
INIT_MODE=quick
```

**INIT_MODE 옵션:**
- `quick` - 주요 종목, 1년치 (~20MB, 5~10분) ⭐ **무료 플랜 권장**
- `us-only` - 미국만 (~48MB, 10분)
- `kr-only` - 한국만 (~490MB, 타임아웃 위험)
- `full` - 전체 (~700MB, **타임아웃 위험 높음**)

## 5. 배포 시작
1. "Create Web Service" 클릭
2. 빌드 및 배포 프로세스 자동 시작
3. 로그에서 진행 상황 확인

## 6. 배포 완료 후 확인사항
- URL 접속하여 사이트 동작 확인
- Admin 페이지 접속 가능 확인
- 데이터베이스 연결 확인

## 7. 초기 데이터 로딩 (중요! ⭐)

배포 완료 후 주식 데이터를 수집해야 합니다.

### Render Shell에서 실행 (권장)

1. Render Dashboard → 해당 Web Service → **"Shell"** 클릭
2. Shell에서 다음 명령어 실행:

**빠른 초기화 (권장, 무료 플랜):**
```bash
python manage.py init_data --quick
```
- 주요 종목만 (한국 5개, 미국 7개)
- 1년치 데이터
- 약 10~20 MB, 5~10분 소요

**한국 주요 시장 (KOSPI):**
```bash
python manage.py init_data --kr-markets "KOSPI" --skip-us
```
- KOSPI 전체, 3년치
- 약 200~300 MB, 30~60분 소요

**전체 데이터 (유료 플랜):**
```bash
python manage.py init_data
```
- 한국 전체 + 미국 S&P500/NASDAQ100
- 약 700 MB, 1~2시간 소요

### Cron Job 설정 (일일 자동 업데이트)

1. Render Dashboard → "New +" → "Cron Job"
2. 다음 설정:
   - Name: `daily-stock-update`
   - Build Command: `pip install -r requirements.txt`
   - Command: `python manage.py daily_update`
   - Schedule: `0 18 * * *` (매일 오후 6시 UTC)
   - Environment: Web Service와 동일한 환경 변수 연결

3. "Create Cron Job" 클릭

**자세한 설정 방법은 `RENDER_AUTOMATION.md` 참고**

## 8. Superuser 생성 (필요시)
Render Shell에서 실행:
```bash
python manage.py createsuperuser
```

## 문제 해결

### 정적 파일이 로드되지 않는 경우
- WhiteNoise가 올바르게 설정되었는지 확인
- `python manage.py collectstatic` 실행 여부 확인

### 데이터베이스 연결 오류
- DATABASE_URL 환경 변수가 올바른지 확인
- PostgreSQL 서비스가 같은 Region에 있는지 확인

### 500 에러
- 로그 확인: Render Dashboard의 Logs 탭
- DEBUG=True로 임시 변경하여 에러 메시지 확인 (프로덕션에서는 다시 False로!)

## 추가 설정

### 커스텀 도메인 연결
1. Render Dashboard → Settings → Custom Domains
2. 도메인 추가 및 DNS 설정

### Auto-Deploy 설정
1. Settings → "Auto-Deploy" 활성화
2. GitHub push 시 자동 배포

## 로컬 개발 환경

로컬에서 개발 시:
1. `.env` 파일 생성 (`.env.example` 참고)
2. 로컬 PostgreSQL 설정
3. `DEBUG=True`로 설정
4. `python manage.py runserver`로 실행

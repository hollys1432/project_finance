# 로컬에서 Render 프로덕션 DB 연결 가이드

Render 무료 플랜은 Shell이 지원되지 않으므로, 로컬에서 프로덕션 데이터베이스에 연결하여 초기 데이터를 로딩할 수 있습니다.

---

## 🔐 주의사항

**⚠️ 프로덕션 데이터베이스에 직접 연결하는 것은 위험할 수 있습니다!**
- 실수로 데이터 삭제 가능
- 잘못된 데이터 입력 가능
- 신중하게 진행하세요

---

## 📋 단계별 가이드

### Step 1: Render PostgreSQL External URL 가져오기

1. Render Dashboard → PostgreSQL 서비스 선택
2. "Info" 탭에서 **External Database URL** 복사
   - 형식: `postgres://user:password@host:port/dbname`

⚠️ Internal URL이 아닌 **External URL**을 사용해야 합니다!

---

### Step 2: 로컬 환경 변수 설정

`.env.production` 파일 생성:

```env
# 프로덕션 데이터베이스 연결
DATABASE_URL=<Render PostgreSQL External URL>

# 기타 설정
SECRET_KEY=<프로덕션과 동일한 SECRET_KEY>
DEBUG=False
ALLOWED_HOSTS=.render.com,localhost
```

---

### Step 3: 로컬에서 프로덕션 DB 연결

**옵션 A: 환경 변수 파일 사용**

```bash
# .env.production을 .env로 임시 복사
cp .env.production .env

# 또는 Windows
copy .env.production .env

# 마이그레이션 확인
python manage.py migrate

# 초기 데이터 로딩
python manage.py init_data --quick

# 완료 후 원래 .env로 복원
git checkout .env
```

**옵션 B: 명령줄에서 직접 지정 (Windows)**

```bash
# PowerShell
$env:DATABASE_URL="<External URL>"
python manage.py init_data --quick

# CMD
set DATABASE_URL=<External URL>
python manage.py init_data --quick
```

**옵션 C: 일시적으로 settings.py 수정**

```python
# config/settings.py에 임시로 추가
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'your_host.oregon-postgres.render.com',
        'PORT': '5432',
    }
}
```

⚠️ **절대로 이 변경사항을 커밋하지 마세요!**

---

### Step 4: 데이터 수집 실행

```bash
# 빠른 초기화
python manage.py init_data --quick

# 또는 커스텀 옵션
python manage.py init_data --kr-markets "KOSPI" --skip-us
```

---

### Step 5: 확인

```bash
python manage.py shell
```

```python
from stocks.models import CompanyInfo, USCompanyInfo
print(f"한국: {CompanyInfo.objects.count()}개")
print(f"미국: {USCompanyInfo.objects.count()}개")
```

---

## 🔒 보안 주의사항

1. **External URL 노출 금지**
   - GitHub에 절대 푸시하지 마세요
   - `.env.production` 파일은 `.gitignore`에 추가

2. **작업 후 정리**
   - 프로덕션 DB URL 삭제
   - 로컬 `.env` 복원

3. **백업**
   - 중요한 작업 전에 DB 백업 권장

---

## 🚨 문제 해결

### 연결 실패
**증상:** `could not connect to server`

**해결:**
- External URL을 사용했는지 확인 (Internal URL은 Render 내부에서만 사용 가능)
- 방화벽이나 VPN이 PostgreSQL 포트(5432)를 차단하지 않는지 확인
- URL 형식이 올바른지 확인

### 타임아웃
**증상:** 연결이 매우 느리거나 타임아웃

**해결:**
- 네트워크 상태 확인
- Render PostgreSQL 서비스가 활성 상태인지 확인
- 무료 플랜은 일정 시간 사용하지 않으면 sleep 모드로 전환됨

---

## 💡 추천 방법

### 무료 플랜 사용자

**빌드 시 자동 로딩이 더 안전합니다:**

Render 환경 변수:
```
INIT_DATA=true
INIT_MODE=quick
```

이 방법이:
- ✅ 더 안전 (로컬에서 프로덕션 접근 불필요)
- ✅ 자동화 (배포 시 자동 실행)
- ✅ 간단 (환경 변수만 설정)

### 유료 플랜 사용자

**Shell 사용이 가장 편리합니다:**
```bash
# Render Shell에서 직접 실행
python manage.py init_data --quick
```

---

## 📊 비교

| 방법 | 무료 플랜 | 안전성 | 편의성 |
|------|-----------|--------|--------|
| **빌드 시 자동 로딩** | ✅ | ⭐⭐⭐ | ⭐⭐⭐ |
| **로컬에서 연결** | ✅ | ⭐⭐ | ⭐⭐ |
| **Render Shell** | ❌ (유료만) | ⭐⭐⭐ | ⭐⭐⭐ |

**결론: 무료 플랜이라면 빌드 시 자동 로딩을 권장합니다!**

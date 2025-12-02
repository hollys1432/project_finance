# Bad Request (400) 에러 디버깅 가이드

Render 배포 후 400 에러가 발생하는 경우 확인 사항입니다.

---

## 🔍 원인 확인 방법

### 1. Render Logs 확인

Render Dashboard → Logs 탭에서 에러 메시지 확인:

```
Invalid HTTP_HOST header: 'project-finance-9zsy.onrender.com'.
You may need to add 'project-finance-9zsy.onrender.com' to ALLOWED_HOSTS.
```

---

## ✅ 해결 방법

### 방법 1: ALLOWED_HOSTS를 * 으로 설정 (빠른 테스트용)

**Render Environment 변수:**
```
ALLOWED_HOSTS=*
```

**장점:**
- ✅ 즉시 해결
- ✅ 간단함

**단점:**
- ⚠️ 보안상 좋지 않음 (프로덕션에서는 비권장)

---

### 방법 2: 특정 도메인만 허용 (권장)

**Render Environment 변수:**
```
ALLOWED_HOSTS=.render.com,project-finance-9zsy.onrender.com
```

**설명:**
- `.render.com` → 모든 Render 서브도메인 허용
- `project-finance-9zsy.onrender.com` → 특정 URL 허용

---

### 방법 3: 코드에서 자동 감지 (이미 적용됨 ✅)

settings.py:
```python
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
```

**Render가 자동으로 제공하는 환경 변수:**
- `RENDER_EXTERNAL_HOSTNAME` → 실제 배포 URL

---

## 🚨 여전히 해결 안 될 때

### DEBUG 모드로 상세 에러 확인

**⚠️ 주의: 프로덕션에서는 절대 DEBUG=True로 두지 마세요!**

1. **임시로** Render Environment에서:
   ```
   DEBUG=True
   ```

2. 배포 후 URL 접속

3. **상세한 에러 메시지 확인**

4. 에러 확인 후 **즉시 다시 False로 변경:**
   ```
   DEBUG=False
   ```

---

## 📋 확인 체크리스트

- [ ] ALLOWED_HOSTS 환경 변수가 올바르게 설정되었는가?
- [ ] Render가 재배포되었는가?
- [ ] Logs에 에러 메시지가 있는가?
- [ ] 실제 URL이 환경 변수에 포함되어 있는가?

---

## 🎯 권장 최종 설정

### Render Environment Variables

```env
SECRET_KEY=<your-secret-key>
DEBUG=False
ALLOWED_HOSTS=.render.com
DATABASE_URL=<postgresql-url>
INIT_DATA=false
```

### settings.py (이미 적용됨)

```python
# Render 환경 자동 감지
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
```

이렇게 하면:
- ✅ 자동으로 Render URL 추가
- ✅ 로컬 개발도 가능
- ✅ 보안 유지

---

## 💡 기타 400 에러 원인

### 1. CSRF 관련
```python
# settings.py에서 확인
CSRF_TRUSTED_ORIGINS = [
    'https://*.render.com',
    'https://project-finance-9zsy.onrender.com',
]
```

### 2. 잘못된 요청 헤더
- User-Agent 없음
- 비정상적인 HTTP 요청

### 3. 미들웨어 문제
- SecurityMiddleware 설정 오류

---

대부분의 경우 ALLOWED_HOSTS 설정으로 해결됩니다!

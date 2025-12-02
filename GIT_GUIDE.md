# Git 명령어 가이드

프로젝트 관리를 위한 필수 Git 명령어 모음입니다.

## 📋 목차
1. [기본 개념](#1-기본-개념)
2. [초기 설정](#2-초기-설정)
3. [일상적인 작업 흐름](#3-일상적인-작업-흐름)
4. [브랜치 관리](#4-브랜치-관리)
5. [되돌리기](#5-되돌리기)
6. [원격 저장소](#6-원격-저장소)
7. [유용한 팁](#7-유용한-팁)
8. [자주 하는 실수와 해결법](#8-자주-하는-실수와-해결법)

---

## 1. 기본 개념

### Git의 3가지 영역

```
Working Directory  →  Staging Area  →  Repository
   (작업 공간)         (준비 영역)       (저장소)
      ↓                   ↓               ↓
   수정된 파일         git add         git commit
```

- **Working Directory**: 실제 파일을 수정하는 곳
- **Staging Area**: 커밋할 파일을 준비하는 곳
- **Repository**: 커밋이 저장되는 곳

---

## 2. 초기 설정

### 처음 한 번만 설정

```bash
# 사용자 정보 설정
git config --global user.name "당신의이름"
git config --global user.email "your.email@example.com"

# 설정 확인
git config --list
```

### 새 프로젝트 시작

```bash
# 기존 폴더를 Git 저장소로 만들기
git init

# 원격 저장소와 연결
git remote add origin https://github.com/username/repository.git

# 원격 저장소 확인
git remote -v
```

---

## 3. 일상적인 작업 흐름

### 3.1 상태 확인

```bash
# 현재 상태 확인 (가장 자주 쓰는 명령어!)
git status

# 간단한 형태로 보기
git status --short
# M  = Modified (수정됨)
# A  = Added (추가됨)
# ?? = Untracked (추적 안 됨)
```

### 3.2 변경사항 확인

```bash
# 수정된 내용 자세히 보기
git diff

# 특정 파일만 보기
git diff config/settings.py

# Staging된 파일 변경사항 보기
git diff --staged
```

### 3.3 파일 추가 (Staging)

```bash
# 특정 파일 추가
git add filename.py

# 여러 파일 추가
git add file1.py file2.py file3.py

# 특정 폴더 전체 추가
git add stocks/

# 현재 디렉토리의 모든 변경사항 추가
git add .

# 모든 변경사항 추가 (삭제된 파일 포함)
git add -A
```

### 3.4 커밋

```bash
# 간단한 메시지로 커밋
git commit -m "Add user authentication feature"

# 여러 줄 메시지로 커밋
git commit -m "Add user authentication

- Implement login/logout
- Add password encryption
- Create user session management"

# add + commit 한 번에 (이미 추적 중인 파일만)
git commit -am "Fix typo in README"
```

### 3.5 원격 저장소에 업로드

```bash
# origin의 main 브랜치에 푸시
git push origin main

# 현재 브랜치를 origin에 푸시
git push

# 처음 푸시할 때 (업스트림 설정)
git push -u origin main
```

### 3.6 원격 저장소에서 다운로드

```bash
# 원격 저장소의 최신 변경사항 가져오기 + 병합
git pull origin main

# 현재 브랜치에 pull
git pull

# 변경사항만 가져오기 (병합 안 함)
git fetch origin
```

---

## 4. 브랜치 관리

### 4.1 브랜치 보기

```bash
# 로컬 브랜치 목록
git branch

# 원격 브랜치 포함 전체 목록
git branch -a

# 각 브랜치의 마지막 커밋 보기
git branch -v
```

### 4.2 브랜치 생성 및 이동

```bash
# 새 브랜치 생성
git branch feature-login

# 브랜치 이동
git checkout feature-login

# 생성 + 이동 한 번에
git checkout -b feature-login

# 최신 Git 문법 (권장)
git switch feature-login
git switch -c feature-login  # 생성 + 이동
```

### 4.3 브랜치 병합

```bash
# main 브랜치로 이동
git checkout main

# feature-login 브랜치를 main에 병합
git merge feature-login

# 병합 완료 후 브랜치 삭제
git branch -d feature-login

# 강제 삭제
git branch -D feature-login
```

### 4.4 실전 예시: 새 기능 개발

```bash
# 1. 새 브랜치 만들고 이동
git checkout -b feature-reports

# 2. 코드 작성...
# (reports 기능 개발)

# 3. 커밋
git add reports/
git commit -m "Add reports feature"

# 4. main으로 돌아가기
git checkout main

# 5. 최신 상태로 업데이트
git pull origin main

# 6. feature 브랜치 병합
git merge feature-reports

# 7. 원격에 푸시
git push origin main

# 8. 작업 브랜치 삭제
git branch -d feature-reports
```

---

## 5. 되돌리기

### 5.1 Staging 취소 (add 취소)

```bash
# 특정 파일 unstage
git restore --staged filename.py

# 모든 파일 unstage
git restore --staged .

# 이전 방식 (여전히 작동)
git reset HEAD filename.py
```

### 5.2 작업 내용 취소 (수정 전으로 되돌리기)

```bash
# 특정 파일의 수정 취소 (위험! 복구 불가)
git restore filename.py

# 모든 수정 취소 (위험!)
git restore .

# 이전 방식
git checkout -- filename.py
```

### 5.3 커밋 되돌리기

```bash
# 가장 최근 커밋 취소 (변경사항은 유지)
git reset --soft HEAD~1

# 가장 최근 커밋 취소 (Staging도 취소, 파일은 유지)
git reset HEAD~1
# 또는
git reset --mixed HEAD~1

# 가장 최근 커밋 완전 취소 (변경사항도 삭제, 위험!)
git reset --hard HEAD~1

# 최근 3개 커밋 취소
git reset HEAD~3
```

### 5.4 커밋 메시지 수정

```bash
# 가장 최근 커밋 메시지 수정
git commit --amend -m "New commit message"

# 파일 추가하고 커밋 수정 (커밋 메시지는 유지)
git add forgotten_file.py
git commit --amend --no-edit
```

### 5.5 특정 커밋으로 되돌리기

```bash
# 커밋 히스토리 보기
git log --oneline

# 특정 커밋으로 되돌리기
git reset --hard abc1234

# 특정 커밋의 변경사항만 취소 (새 커밋 생성)
git revert abc1234
```

---

## 6. 원격 저장소

### 6.1 원격 저장소 관리

```bash
# 원격 저장소 목록
git remote -v

# 원격 저장소 추가
git remote add origin https://github.com/username/repo.git

# 원격 저장소 URL 변경
git remote set-url origin https://github.com/username/new-repo.git

# 원격 저장소 삭제
git remote remove origin
```

### 6.2 원격 브랜치

```bash
# 원격 브랜치 목록
git branch -r

# 원격 브랜치 가져오기
git checkout -b local-branch origin/remote-branch

# 원격 브랜치 삭제
git push origin --delete feature-branch
```

### 6.3 GitHub에서 저장소 클론

```bash
# HTTPS 방식
git clone https://github.com/username/repository.git

# 특정 폴더 이름으로 클론
git clone https://github.com/username/repository.git my-project

# 특정 브랜치만 클론
git clone -b develop https://github.com/username/repository.git
```

---

## 7. 유용한 팁

### 7.1 로그 보기

```bash
# 간단한 로그
git log --oneline

# 최근 5개만
git log --oneline -5

# 그래프로 보기
git log --oneline --graph --all

# 특정 파일의 히스토리
git log --oneline -- config/settings.py

# 누가 언제 수정했는지 보기
git blame config/settings.py
```

### 7.2 .gitignore

```bash
# .gitignore 파일 생성
touch .gitignore

# 예시 내용
# Python
__pycache__/
*.pyc
*.pyo
.env
.env.local
*.log

# Django
db.sqlite3
/staticfiles/
/media/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

### 7.3 이미 커밋된 파일 무시하기

```bash
# .gitignore에 추가한 후
git rm --cached filename.py

# 폴더 전체
git rm --cached -r folder/

# 커밋
git commit -m "Remove tracked files from .gitignore"
```

### 7.4 임시 저장 (Stash)

```bash
# 현재 작업 임시 저장
git stash

# 메시지와 함께 저장
git stash save "WIP: working on login feature"

# 저장 목록 보기
git stash list

# 가장 최근 stash 복원
git stash pop

# 특정 stash 복원
git stash apply stash@{1}

# stash 삭제
git stash drop stash@{0}

# 모든 stash 삭제
git stash clear
```

---

## 8. 자주 하는 실수와 해결법

### 8.1 잘못된 브랜치에 커밋했을 때

```bash
# main에 커밋했는데 feature 브랜치에 했어야 했을 때

# 1. 새 브랜치 생성 (현재 커밋 포함)
git branch feature-branch

# 2. main을 이전 상태로 되돌리기
git reset --hard HEAD~1

# 3. feature 브랜치로 이동
git checkout feature-branch
```

### 8.2 .env 파일을 실수로 커밋했을 때

```bash
# 1. .gitignore에 추가
echo ".env" >> .gitignore

# 2. Git에서 제거 (파일은 유지)
git rm --cached .env

# 3. 커밋
git commit -m "Remove .env from tracking"

# 4. 푸시
git push origin main

# 주의: 이미 푸시한 경우 히스토리에 남아있음!
# 민감한 정보는 즉시 변경 필요 (SECRET_KEY 등)
```

### 8.3 Merge Conflict 해결

```bash
# 병합 중 충돌 발생
git merge feature-branch
# CONFLICT (content): Merge conflict in config/settings.py

# 1. 충돌 파일 확인
git status

# 2. 파일을 열어서 수동으로 수정
# <<<<<<< HEAD
# 현재 브랜치 내용
# =======
# 병합하려는 브랜치 내용
# >>>>>>> feature-branch

# 3. 충돌 해결 후 저장

# 4. 해결된 파일 add
git add config/settings.py

# 5. 병합 커밋 완료
git commit -m "Merge feature-branch and resolve conflicts"
```

### 8.4 푸시가 거부당했을 때

```bash
# 오류: ! [rejected] main -> main (fetch first)

# 원인: 원격에 새로운 커밋이 있음

# 해결 1: Pull 후 Push
git pull origin main
git push origin main

# 해결 2: Rebase 사용 (더 깔끔한 히스토리)
git pull --rebase origin main
git push origin main
```

### 8.5 실수로 파일 삭제했을 때

```bash
# 파일 복구 (아직 커밋 안 함)
git restore deleted_file.py

# 특정 커밋에서 파일 복구
git checkout abc1234 -- deleted_file.py
```

### 8.6 Push한 커밋 되돌리기

```bash
# 방법 1: Revert (안전, 권장)
git revert HEAD
git push origin main

# 방법 2: Force Push (위험! 협업 시 주의)
git reset --hard HEAD~1
git push --force origin main

# 경고: Force push는 팀원의 작업을 망칠 수 있음!
```

---

## 9. 실전 시나리오

### 시나리오 1: 일반적인 작업 흐름

```bash
# 아침에 출근해서
git pull origin main

# 작업 시작
git checkout -b feature-new-dashboard

# 코드 작성...
# (파일 수정, 생성)

# 중간 저장
git add .
git status
git commit -m "WIP: Add dashboard layout"

# 더 작업...

# 완성
git add .
git commit -m "Complete dashboard feature with charts"

# main에 병합
git checkout main
git pull origin main
git merge feature-new-dashboard
git push origin main

# 브랜치 정리
git branch -d feature-new-dashboard
```

### 시나리오 2: 급하게 버그 수정

```bash
# 현재 작업 중이었는데 급한 버그 발견

# 1. 현재 작업 임시 저장
git stash save "WIP: developing feature X"

# 2. main으로 이동
git checkout main

# 3. 버그 수정 브랜치 생성
git checkout -b hotfix-login-bug

# 4. 버그 수정
# (코드 수정)

# 5. 커밋 및 병합
git add .
git commit -m "Fix login validation bug"
git checkout main
git merge hotfix-login-bug
git push origin main

# 6. 원래 작업으로 복귀
git checkout feature-x
git stash pop
```

### 시나리오 3: Render 배포용 작업

```bash
# 1. 배포 준비 파일 추가
git add render.yaml RENDER_NEON_DEPLOY.md
git add .gitignore

# 2. 설정 파일 변경사항 확인
git diff config/settings.py

# 3. 모두 추가
git add config/settings.py config/urls.py

# 4. 상태 확인 (.env.production이 추적 안 되는지 확인!)
git status

# 5. 커밋
git commit -m "Add Render + Neon deployment configuration

- Add render.yaml for Blueprint deployment
- Add deployment guide
- Update .gitignore to exclude sensitive files"

# 6. 푸시
git push origin main

# 7. Render에서 자동 배포 시작!
```

---

## 10. 자주 쓰는 명령어 치트시트

```bash
# === 상태 확인 ===
git status                  # 현재 상태
git log --oneline          # 커밋 히스토리
git diff                   # 변경사항 보기

# === 기본 작업 ===
git add .                  # 모든 변경사항 추가
git commit -m "message"    # 커밋
git push origin main       # 푸시
git pull origin main       # 풀

# === 브랜치 ===
git branch                 # 브랜치 목록
git checkout -b new-branch # 브랜치 생성 + 이동
git merge feature-branch   # 브랜치 병합

# === 되돌리기 ===
git restore --staged file  # unstage
git restore file           # 수정 취소
git reset HEAD~1           # 커밋 취소 (변경사항 유지)

# === 임시 저장 ===
git stash                  # 임시 저장
git stash pop              # 복원

# === 원격 ===
git remote -v              # 원격 저장소 확인
git clone <url>            # 클론
```

---

## 참고 자료

- **공식 문서**: https://git-scm.com/doc
- **Git 치트시트**: https://education.github.com/git-cheat-sheet-education.pdf
- **Interactive 튜토리얼**: https://learngitbranching.js.org/

---

## 도움말

```bash
# 명령어 도움말 보기
git help
git help commit
git help branch

# 짧은 도움말
git commit -h
```

---

**팁**: Git 명령어가 헷갈릴 때는 `git status`를 자주 실행하세요.
현재 상태와 함께 다음에 할 수 있는 명령어를 친절하게 알려줍니다! 🚀

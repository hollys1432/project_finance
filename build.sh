#!/usr/bin/env bash
# exit on error
set -o errexit

echo "=========================================="
echo "Render Build Script"
echo "=========================================="

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations
echo "Running migrations..."
python manage.py migrate

# 초기 데이터 로딩 (환경 변수로 제어)
if [ "$INIT_DATA" = "true" ]; then
    echo "=========================================="
    echo "초기 데이터 로딩 시작..."
    echo "=========================================="

    # INIT_MODE에 따라 다른 모드로 실행
    if [ "$INIT_MODE" = "quick" ]; then
        echo "빠른 초기화 모드 (주요 종목, 1년치)"
        python manage.py init_data --quick
    elif [ "$INIT_MODE" = "kr-only" ]; then
        echo "한국 종목만 초기화"
        python manage.py init_data --skip-us
    elif [ "$INIT_MODE" = "us-only" ]; then
        echo "미국 종목만 초기화"
        python manage.py init_data --skip-kr
    else
        echo "전체 초기화 (3년치 데이터)"
        python manage.py init_data
    fi

    echo "초기 데이터 로딩 완료"
else
    echo "초기 데이터 로딩 건너뛰기 (INIT_DATA 환경 변수가 설정되지 않음)"
    echo "데이터를 로딩하려면 Render Shell에서 다음 명령어를 실행하세요:"
    echo "  python manage.py init_data --quick"
fi

echo "=========================================="
echo "Build 완료!"
echo "=========================================="

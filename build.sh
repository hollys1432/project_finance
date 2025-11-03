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

echo "=========================================="
echo "Build 완료!"
echo "=========================================="
echo ""
echo "📊 데이터 수집 안내:"
echo "로컬에서 프로덕션 DB에 연결하여 데이터를 수집하세요."
echo ""
echo "1. Render Dashboard에서 External Database URL 복사"
echo "2. 로컬 .env 파일에 DATABASE_URL 설정"
echo "3. 데이터 수집 명령어 실행:"
echo "   - 한국 주식: python manage.py kr_step01_get_companyinfo"
echo "   - 한국 가격: python manage.py kr_step02_get_past_price"
echo "   - 미국 주식: python manage.py create_us_basic"
echo "   - 미국 가격: python manage.py us_step02_get_past_price --start 2024-01-01"
echo ""
echo "자세한 내용은 LOCAL_TO_PRODUCTION_GUIDE.md를 참고하세요."
echo "=========================================="

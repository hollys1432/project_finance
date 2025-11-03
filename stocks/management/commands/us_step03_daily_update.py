"""
미국 주식 데이터 일간 업데이트용 스크립트
크론잡이나 스케줄러에서 매일 실행하기 위한 간단한 wrapper
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "미국 주식 데이터 일간 업데이트 (회사정보 + 가격데이터)"

    def add_arguments(self, parser):
        parser.add_argument("--skip-company-update", action="store_true", 
                          help="회사 정보 업데이트 건너뛰기")
        parser.add_argument("--price-only", action="store_true", 
                          help="가격 데이터만 업데이트")

    def handle(self, *args, **options):
        skip_company = options["skip_company_update"]
        price_only = options["price_only"]
        
        if not price_only and not skip_company:
            self.stdout.write("1. 회사 정보 업데이트...")
            try:
                call_command('us_step01_get_company_info', '--update', '--ignore-conflicts')
                self.stdout.write(self.style.SUCCESS("회사 정보 업데이트 완료"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"회사 정보 업데이트 실패: {e}"))

        self.stdout.write("2. 가격 데이터 증분 수집...")
        try:
            call_command('us_step02_get_past_price', '--only-latest')
            self.stdout.write(self.style.SUCCESS("가격 데이터 업데이트 완료"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"가격 데이터 업데이트 실패: {e}"))

        self.stdout.write(self.style.SUCCESS("일간 업데이트 완료!"))


# === requirements.txt 추가 사항 ===
"""
기존 requirements.txt에 추가:

yfinance>=0.2.18
pandas>=1.5.0
"""

# === 사용법 예시 ===
"""
# 1. 회사 정보 수집
python manage.py us_step01_get_company_info --sp500 --nasdaq100
python manage.py us_step01_get_company_info --symbols="AAPL,GOOGL,MSFT"
python manage.py us_step01_get_company_info --dry-run

# 2. 과거 가격 데이터 수집
python manage.py us_step02_get_past_price --full-history
python manage.py us_step02_get_past_price --symbols="AAPL,GOOGL"
python manage.py us_step02_get_past_price --start=2020-01-01 --end=2023-12-31

# 3. 일간 업데이트 (크론잡용)
python manage.py us_step03_daily_update

# 마이그레이션
python manage.py makemigrations
python manage.py migrate
"""

# === 추가 유틸리티: 데이터 검증 스크립트 ===
from django.core.management.base import BaseCommand
from django.db.models import Count, Max, Min
from stocks.models import USCompanyInfo, USPriceData


class DataValidationCommand(BaseCommand):
    """데이터 품질 검증을 위한 유틸리티 명령어"""
    help = "미국 주식 데이터 품질 검증 및 통계"

    def handle(self, *args, **options):
        # 회사 수 통계
        company_count = USCompanyInfo.objects.count()
        active_count = USCompanyInfo.objects.filter(is_active=True).count()
        
        self.stdout.write(f"등록된 회사 수: {company_count}개 (활성: {active_count}개)")
        
        # 섹터별 통계
        sectors = USCompanyInfo.objects.values('sector').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        self.stdout.write("\n주요 섹터별 회사 수:")
        for sector in sectors:
            name = sector['sector'] or '미분류'
            self.stdout.write(f"  {name}: {sector['count']}개")
        
        # 가격 데이터 통계
        price_stats = USPriceData.objects.aggregate(
            total_records=Count('id'),
            earliest_date=Min('date'),
            latest_date=Max('date'),
            companies_with_data=Count('stock', distinct=True)
        )
        
        self.stdout.write(f"\n가격 데이터 통계:")
        self.stdout.write(f"  총 레코드 수: {price_stats['total_records']:,}건")
        self.stdout.write(f"  데이터 보유 회사 수: {price_stats['companies_with_data']}개")
        self.stdout.write(f"  데이터 기간: {price_stats['earliest_date']} ~ {price_stats['latest_date']}")
        
        # 최근 데이터 누락 종목 확인
        from datetime import datetime, timedelta
        recent_date = datetime.now().date() - timedelta(days=7)  # 1주일 전
        
        companies_without_recent = USCompanyInfo.objects.filter(
            is_active=True
        ).exclude(
            prices__date__gte=recent_date
        ).count()
        
        self.stdout.write(f"  최근 1주일 데이터 누락 종목: {companies_without_recent}개")
        
        if companies_without_recent > 0:
            self.stdout.write(self.style.WARNING(
                "  → 일간 업데이트 스크립트 실행을 권장합니다."
            ))
# stocks/management/commands/create_us_basic.py
"""
미국 주요 종목 기본 정보를 수동으로 생성하는 명령어
Yahoo Finance API 제한을 우회하여 빠르게 기본 데이터 입력
"""
from django.core.management.base import BaseCommand
from stocks.models import USCompanyInfo


class Command(BaseCommand):
    help = "미국 주요 종목 기본 정보 생성 (API 없이)"

    def handle(self, *args, **options):
        # 주요 종목 기본 정보
        companies = [
            {
                'symbol': 'AAPL',
                'company_name': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'exchange': 'NASDAQ',
                'country': 'US',
                'currency': 'USD',
            },
            {
                'symbol': 'GOOGL',
                'company_name': 'Alphabet Inc.',
                'sector': 'Technology',
                'industry': 'Internet Content & Information',
                'exchange': 'NASDAQ',
                'country': 'US',
                'currency': 'USD',
            },
            {
                'symbol': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'sector': 'Technology',
                'industry': 'Software - Infrastructure',
                'exchange': 'NASDAQ',
                'country': 'US',
                'currency': 'USD',
            },
            {
                'symbol': 'TSLA',
                'company_name': 'Tesla, Inc.',
                'sector': 'Consumer Cyclical',
                'industry': 'Auto Manufacturers',
                'exchange': 'NASDAQ',
                'country': 'US',
                'currency': 'USD',
            },
            {
                'symbol': 'NVDA',
                'company_name': 'NVIDIA Corporation',
                'sector': 'Technology',
                'industry': 'Semiconductors',
                'exchange': 'NASDAQ',
                'country': 'US',
                'currency': 'USD',
            },
            {
                'symbol': 'AMZN',
                'company_name': 'Amazon.com, Inc.',
                'sector': 'Consumer Cyclical',
                'industry': 'Internet Retail',
                'exchange': 'NASDAQ',
                'country': 'US',
                'currency': 'USD',
            },
            {
                'symbol': 'META',
                'company_name': 'Meta Platforms, Inc.',
                'sector': 'Technology',
                'industry': 'Internet Content & Information',
                'exchange': 'NASDAQ',
                'country': 'US',
                'currency': 'USD',
            },
        ]

        created = 0
        updated = 0

        for data in companies:
            company, is_created = USCompanyInfo.objects.update_or_create(
                symbol=data['symbol'],
                defaults={
                    'company_name': data['company_name'],
                    'sector': data.get('sector'),
                    'industry': data.get('industry'),
                    'exchange': data.get('exchange'),
                    'country': data.get('country', 'US'),
                    'currency': data.get('currency', 'USD'),
                    'is_active': True,
                }
            )

            if is_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ {data["symbol"]} 생성'))
            else:
                updated += 1
                self.stdout.write(self.style.WARNING(f'→ {data["symbol"]} 업데이트'))

        self.stdout.write(self.style.SUCCESS(f'\n완료: 생성 {created}개, 업데이트 {updated}개'))

# stocks/management/commands/init_data.py
"""
초기 데이터 로딩 명령어
Render 배포 시 자동으로 기본 데이터를 수집합니다.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from stocks.models import CompanyInfo, USCompanyInfo
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "초기 데이터 로딩: 기업 정보 및 가격 데이터 수집 (3년치)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-kr',
            action='store_true',
            help='한국 주식 수집 건너뛰기'
        )
        parser.add_argument(
            '--skip-us',
            action='store_true',
            help='미국 주식 수집 건너뛰기'
        )
        parser.add_argument(
            '--kr-markets',
            type=str,
            default='KOSPI',
            help='한국 시장 지정 (기본: KOSPI, 예: KOSPI,KOSDAQ)'
        )
        parser.add_argument(
            '--us-symbols',
            type=str,
            default=None,
            help='미국 주요 종목만 (쉼표 구분, 예: AAPL,GOOGL,MSFT)'
        )
        parser.add_argument(
            '--quick',
            action='store_true',
            help='빠른 초기화: 최소한의 데이터만 수집 (주요 종목, 1년치)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 데이터가 있어도 강제 실행'
        )

    def handle(self, *args, **options):
        skip_kr = options['skip_kr']
        skip_us = options['skip_us']
        kr_markets = options['kr_markets']
        us_symbols = options['us_symbols']
        quick = options['quick']
        force = options['force']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('초기 데이터 로딩 시작'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # 기존 데이터 확인
        if not force:
            kr_count = CompanyInfo.objects.count()
            us_count = USCompanyInfo.objects.count()

            if kr_count > 0 or us_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n이미 데이터가 존재합니다 (한국: {kr_count}개, 미국: {us_count}개)'
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        '강제 실행하려면 --force 옵션을 사용하세요.\n'
                    )
                )
                return

        # Quick 모드 설정
        if quick:
            self.stdout.write(self.style.NOTICE('\n🚀 빠른 초기화 모드'))
            self.stdout.write('  - 주요 종목만 수집')
            self.stdout.write('  - 1년치 데이터만 수집\n')

            # 한국 주요 종목
            kr_codes = '005930,000660,035420,051910,035720'  # 삼성전자, SK하이닉스, NAVER, LG화학, 카카오
            # 미국 주요 종목
            if not us_symbols:
                us_symbols = 'AAPL,GOOGL,MSFT,TSLA,NVDA,AMZN,META'

        # 한국 주식 수집
        if not skip_kr:
            self.stdout.write(self.style.SUCCESS('\n[1/4] 한국 기업 정보 수집 중...'))
            try:
                call_command('kr_step01_get_companyinfo')
                self.stdout.write(self.style.SUCCESS('✓ 한국 기업 정보 수집 완료'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'✗ 한국 기업 정보 수집 실패: {e}'))
                logger.exception('한국 기업 정보 수집 실패')

            self.stdout.write(self.style.SUCCESS('\n[2/4] 한국 가격 데이터 수집 중...'))
            try:
                cmd_options = ['kr_step02_get_past_price']

                if quick:
                    # Quick 모드: 주요 종목, 1년치
                    cmd_options.extend(['--codes', kr_codes, '--start', '2024-01-01'])
                else:
                    # 일반 모드: 지정된 시장, 3년치 (기본값)
                    cmd_options.extend(['--markets', kr_markets])

                call_command(*cmd_options)
                self.stdout.write(self.style.SUCCESS('✓ 한국 가격 데이터 수집 완료'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'✗ 한국 가격 데이터 수집 실패: {e}'))
                logger.exception('한국 가격 데이터 수집 실패')

        # 미국 주식 수집
        if not skip_us:
            self.stdout.write(self.style.SUCCESS('\n[3/4] 미국 기업 정보 수집 중...'))
            try:
                cmd_options = ['us_step01_get_company_info']

                if us_symbols:
                    # 특정 종목만
                    cmd_options.extend(['--symbols', us_symbols])
                elif quick:
                    # Quick 모드는 위에서 설정한 주요 종목
                    cmd_options.extend(['--symbols', us_symbols or 'AAPL,GOOGL,MSFT'])
                # else: 기본값 (S&P500 + NASDAQ100)

                call_command(*cmd_options)
                self.stdout.write(self.style.SUCCESS('✓ 미국 기업 정보 수집 완료'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'✗ 미국 기업 정보 수집 실패: {e}'))
                logger.exception('미국 기업 정보 수집 실패')

            self.stdout.write(self.style.SUCCESS('\n[4/4] 미국 가격 데이터 수집 중...'))
            try:
                cmd_options = ['us_step02_get_past_price']

                if us_symbols:
                    cmd_options.extend(['--symbols', us_symbols])

                if quick:
                    # Quick 모드: 1년치
                    cmd_options.extend(['--start', '2024-01-01'])
                # else: 3년치 (기본값)

                call_command(*cmd_options)
                self.stdout.write(self.style.SUCCESS('✓ 미국 가격 데이터 수집 완료'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'✗ 미국 가격 데이터 수집 실패: {e}'))
                logger.exception('미국 가격 데이터 수집 실패')

        # 완료 메시지
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('초기 데이터 로딩 완료!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # 결과 요약
        kr_count = CompanyInfo.objects.count()
        us_count = USCompanyInfo.objects.count()

        self.stdout.write(f'\n📊 수집된 데이터:')
        self.stdout.write(f'  - 한국 기업: {kr_count}개')
        self.stdout.write(f'  - 미국 기업: {us_count}개')

        if kr_count > 0:
            from stocks.models import PriceData
            kr_price_count = PriceData.objects.count()
            self.stdout.write(f'  - 한국 가격 데이터: {kr_price_count:,}건')

        if us_count > 0:
            from stocks.models import USPriceData
            us_price_count = USPriceData.objects.count()
            self.stdout.write(f'  - 미국 가격 데이터: {us_price_count:,}건')

        self.stdout.write('')

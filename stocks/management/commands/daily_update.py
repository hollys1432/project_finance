# stocks/management/commands/daily_update.py
"""
일일 데이터 업데이트 명령어
Render Cron Job으로 실행하여 자동으로 최신 데이터를 수집합니다.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from stocks.models import CompanyInfo, USCompanyInfo
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "일일 데이터 업데이트: 한국/미국 주식의 최신 가격 데이터 증분 수집"

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-kr',
            action='store_true',
            help='한국 주식 업데이트 건너뛰기'
        )
        parser.add_argument(
            '--skip-us',
            action='store_true',
            help='미국 주식 업데이트 건너뛰기'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='상세 로그 출력'
        )

    def handle(self, *args, **options):
        skip_kr = options['skip_kr']
        skip_us = options['skip_us']
        verbose = options['verbose']

        start_time = datetime.now()

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'일일 데이터 업데이트 시작: {start_time.strftime("%Y-%m-%d %H:%M:%S")}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # 데이터 존재 확인
        kr_count = CompanyInfo.objects.count()
        us_count = USCompanyInfo.objects.count()

        if kr_count == 0 and us_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  기업 정보가 없습니다. 먼저 초기 데이터를 로딩하세요:'
                )
            )
            self.stdout.write('  python manage.py init_data --quick\n')
            return

        self.stdout.write(f'\n현재 등록된 기업 수: 한국 {kr_count}개, 미국 {us_count}개\n')

        results = {
            'kr_success': False,
            'us_success': False,
            'kr_error': None,
            'us_error': None,
        }

        # 한국 주식 업데이트
        if not skip_kr and kr_count > 0:
            self.stdout.write(self.style.NOTICE('[1/2] 한국 주식 데이터 업데이트 중...'))
            try:
                # --only-latest: 마지막 저장일 이후 데이터만 증분 수집
                call_command('kr_step02_get_past_price', '--only-latest')
                results['kr_success'] = True
                self.stdout.write(self.style.SUCCESS('✓ 한국 주식 업데이트 완료'))
            except Exception as e:
                results['kr_error'] = str(e)
                self.stderr.write(self.style.ERROR(f'✗ 한국 주식 업데이트 실패: {e}'))
                logger.exception('한국 주식 업데이트 실패')

        # 미국 주식 업데이트
        if not skip_us and us_count > 0:
            self.stdout.write(self.style.NOTICE('\n[2/2] 미국 주식 데이터 업데이트 중...'))
            try:
                # us_step03_daily_update가 있다면 사용, 없으면 --only-latest 사용
                try:
                    call_command('us_step03_daily_update')
                except:
                    # us_step03이 없으면 us_step02 사용
                    call_command('us_step02_get_past_price', '--only-latest')

                results['us_success'] = True
                self.stdout.write(self.style.SUCCESS('✓ 미국 주식 업데이트 완료'))
            except Exception as e:
                results['us_error'] = str(e)
                self.stderr.write(self.style.ERROR(f'✗ 미국 주식 업데이트 실패: {e}'))
                logger.exception('미국 주식 업데이트 실패')

        # 완료 메시지
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('일일 데이터 업데이트 완료!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # 결과 요약
        self.stdout.write(f'\n📊 업데이트 결과:')
        if not skip_kr and kr_count > 0:
            status = '✓' if results['kr_success'] else '✗'
            self.stdout.write(f'  {status} 한국 주식: {"성공" if results["kr_success"] else "실패"}')
            if results['kr_error'] and verbose:
                self.stdout.write(f'     에러: {results["kr_error"]}')

        if not skip_us and us_count > 0:
            status = '✓' if results['us_success'] else '✗'
            self.stdout.write(f'  {status} 미국 주식: {"성공" if results["us_success"] else "실패"}')
            if results['us_error'] and verbose:
                self.stdout.write(f'     에러: {results["us_error"]}')

        self.stdout.write(f'\n⏱️  소요 시간: {duration:.1f}초')
        self.stdout.write(f'🕐 완료 시각: {end_time.strftime("%Y-%m-%d %H:%M:%S")}\n')

        # 에러가 있으면 종료 코드 1 반환
        if results['kr_error'] or results['us_error']:
            raise Exception('일부 업데이트 실패')

"""
일일 보고서 자동 생성 명령어
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from reports.models import MarketReport
from reports.utils.report_generator import MarketAnalyzer


class Command(BaseCommand):
    help = '일일 시장 분석 보고서 생성'

    def add_arguments(self, parser):
        parser.add_argument(
            '--market',
            type=str,
            default='all',
            choices=['kr', 'us', 'all'],
            help='시장 선택 (kr/us/all)'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='보고서 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 보고서가 있어도 강제로 재생성'
        )

    def handle(self, *args, **options):
        market = options['market']
        force = options['force']

        # 날짜 처리
        if options['date']:
            from datetime import datetime
            try:
                report_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR('잘못된 날짜 형식입니다. YYYY-MM-DD 형식을 사용하세요.'))
                return
        else:
            report_date = timezone.now().date()

        self.stdout.write(f'보고서 생성 시작: {report_date} ({market} 시장)')

        # 기존 보고서 확인
        existing_report = MarketReport.objects.filter(
            report_type='daily',
            market=market,
            report_date=report_date
        ).first()

        if existing_report and not force:
            self.stdout.write(self.style.WARNING(
                f'이미 생성된 보고서가 있습니다 (ID: {existing_report.id}). '
                f'재생성하려면 --force 옵션을 사용하세요.'
            ))
            return

        # 분석기 생성
        analyzer = MarketAnalyzer(market=market, report_date=report_date)

        # 데이터 생성
        self.stdout.write('시장 지수 분석 중...')
        market_indices = analyzer.generate_market_indices()

        self.stdout.write('거래량 상위 종목 분석 중...')
        top_volume = analyzer.get_top_volume_stocks(limit=20)

        self.stdout.write('가격 변동률 분석 중...')
        gainers, losers = analyzer.get_top_gainers_losers(limit=20)

        self.stdout.write('섹터 분석 중...')
        sector_analysis = analyzer.get_sector_analysis()

        self.stdout.write('기술적 분석 중...')
        technical_summary = analyzer.get_technical_summary()

        # 보고서 저장 또는 업데이트
        if existing_report and force:
            existing_report.market_indices = market_indices
            existing_report.top_volume_stocks = top_volume
            existing_report.top_gainers = gainers
            existing_report.top_losers = losers
            existing_report.sector_analysis = sector_analysis
            existing_report.technical_summary = technical_summary
            existing_report.save()

            self.stdout.write(self.style.SUCCESS(
                f'보고서가 업데이트되었습니다 (ID: {existing_report.id})'
            ))
        else:
            report = MarketReport.objects.create(
                report_type='daily',
                market=market,
                report_date=report_date,
                market_indices=market_indices,
                top_volume_stocks=top_volume,
                top_gainers=gainers,
                top_losers=losers,
                sector_analysis=sector_analysis,
                technical_summary=technical_summary,
            )

            self.stdout.write(self.style.SUCCESS(
                f'보고서가 생성되었습니다 (ID: {report.id})'
            ))

        # 요약 출력
        self.stdout.write('\n=== 보고서 요약 ===')
        self.stdout.write(f'거래량 상위 종목: {len(top_volume)}개')
        self.stdout.write(f'상승 종목: {len(gainers)}개')
        self.stdout.write(f'하락 종목: {len(losers)}개')

        if sector_analysis:
            self.stdout.write(f'섹터 분석: {len(sector_analysis)}개 섹터')

        if market_indices.get('kr'):
            kr_data = market_indices['kr']
            self.stdout.write(f'\n한국 시장 평균 등락률: {kr_data.get("avg_change", 0)}%')

        if market_indices.get('us'):
            us_data = market_indices['us']
            self.stdout.write(f'미국 시장 평균 등락률: {us_data.get("avg_change", 0)}%')

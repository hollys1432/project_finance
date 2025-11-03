"""
모든 종목에 대한 백테스트 일괄 실행 커맨드
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from stocks.models import CompanyInfo, PriceData, USCompanyInfo, USPriceData
from quant.models import Strategy, Backtest, Signal
from quant.strategies.ma_cross import MovingAverageCrossStrategy
from quant.strategies.rsi_strategy import RSIStrategy
from quant.strategies.bollinger_strategy import BollingerBandsStrategy
from quant.strategies.squeeze_momentum_strategy import SqueezeMomentumStrategy
from quant.backtest import BacktestEngine
from datetime import datetime, timedelta
import pandas as pd
from decimal import Decimal
import time


class Command(BaseCommand):
    help = '모든 종목에 대해 퀀트 전략 백테스트 일괄 실행'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strategy',
            type=str,
            default='ma_cross',
            help='전략 유형 (ma_cross, rsi, bollinger, squeeze_momentum)'
        )
        parser.add_argument(
            '--market',
            type=str,
            default='kr',
            choices=['kr', 'us', 'all'],
            help='시장 선택 (kr: 한국, us: 미국, all: 모두)'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='시작일 (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='종료일 (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--initial-capital',
            type=int,
            default=10000000,
            help='초기 자본금 (기본값: 10000000)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='백테스트할 종목 수 제한 (테스트용)'
        )
        parser.add_argument(
            '--min-data-points',
            type=int,
            default=100,
            help='최소 데이터 포인트 수 (기본값: 100)'
        )

    def handle(self, *args, **options):
        strategy_type = options['strategy']
        market = options['market']
        start_date = options.get('start_date')
        end_date = options.get('end_date')
        initial_capital = options['initial_capital']
        limit = options.get('limit')
        min_data_points = options['min_data_points']

        # 날짜 설정 (기본값: 최근 1년)
        if not end_date:
            end_date = datetime.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        if not start_date:
            start_date = end_date - timedelta(days=365)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

        self.stdout.write(self.style.SUCCESS(f"\n{'='*70}"))
        self.stdout.write(self.style.SUCCESS(f"모든 종목 백테스트 시작"))
        self.stdout.write(self.style.SUCCESS(f"{'='*70}"))
        self.stdout.write(f"전략: {strategy_type}")
        self.stdout.write(f"시장: {market}")
        self.stdout.write(f"기간: {start_date} ~ {end_date}")
        self.stdout.write(f"초기 자본금: {initial_capital:,}원")
        self.stdout.write(f"최소 데이터 포인트: {min_data_points}개")
        if limit:
            self.stdout.write(f"종목 수 제한: {limit}개")
        self.stdout.write(f"{'='*70}\n")

        # 전략 인스턴스 생성
        strategy_instance = self.get_strategy(strategy_type)
        if not strategy_instance:
            self.stdout.write(self.style.ERROR(f"전략 '{strategy_type}'를 찾을 수 없습니다."))
            return

        # 통계
        total_stocks = 0
        success_count = 0
        fail_count = 0
        skip_count = 0

        start_time = time.time()

        # 한국 주식 백테스트
        if market in ['kr', 'all']:
            self.stdout.write(self.style.SUCCESS("\n[한국 주식 백테스트 시작]"))
            kr_companies = CompanyInfo.objects.filter(is_active=True).order_by('company_code')

            if limit:
                kr_companies = kr_companies[:limit]

            total_stocks += kr_companies.count()

            for idx, company in enumerate(kr_companies, 1):
                result = self.run_backtest_for_stock(
                    company, None, strategy_type, strategy_instance,
                    start_date, end_date, initial_capital, min_data_points, idx
                )

                if result == 'success':
                    success_count += 1
                elif result == 'skip':
                    skip_count += 1
                else:
                    fail_count += 1

        # 미국 주식 백테스트
        if market in ['us', 'all']:
            self.stdout.write(self.style.SUCCESS("\n[미국 주식 백테스트 시작]"))
            us_companies = USCompanyInfo.objects.filter(is_active=True).order_by('symbol')

            if limit:
                us_companies = us_companies[:limit]

            total_stocks += us_companies.count()

            for idx, company in enumerate(us_companies, 1):
                result = self.run_backtest_for_stock(
                    None, company, strategy_type, strategy_instance,
                    start_date, end_date, initial_capital, min_data_points, idx
                )

                if result == 'success':
                    success_count += 1
                elif result == 'skip':
                    skip_count += 1
                else:
                    fail_count += 1

        # 최종 결과 출력
        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"\n{'='*70}"))
        self.stdout.write(self.style.SUCCESS("백테스트 완료!"))
        self.stdout.write(self.style.SUCCESS(f"{'='*70}"))
        self.stdout.write(f"총 종목 수: {total_stocks}개")
        self.stdout.write(self.style.SUCCESS(f"성공: {success_count}개"))
        self.stdout.write(self.style.WARNING(f"스킵: {skip_count}개 (데이터 부족)"))
        self.stdout.write(self.style.ERROR(f"실패: {fail_count}개"))
        self.stdout.write(f"소요 시간: {elapsed_time:.1f}초 ({elapsed_time/60:.1f}분)")
        self.stdout.write(self.style.SUCCESS(f"{'='*70}\n"))

    def run_backtest_for_stock(self, kr_stock, us_stock, strategy_type, strategy_instance,
                                start_date, end_date, initial_capital, min_data_points, idx):
        """단일 종목에 대한 백테스트 실행"""

        stock_name = kr_stock.company_name if kr_stock else us_stock.company_name
        stock_code = kr_stock.company_code if kr_stock else us_stock.symbol

        try:
            # 가격 데이터 조회
            df = self.get_price_data(kr_stock, us_stock, start_date, end_date)

            # 데이터 검증
            if df.empty or len(df) < min_data_points:
                self.stdout.write(
                    self.style.WARNING(f"[{idx}] {stock_name} ({stock_code}): 스킵 (데이터 부족: {len(df)}개)")
                )
                return 'skip'

            # 신호 생성
            df_with_signals = strategy_instance.generate_signals(df)

            # 백테스트 실행
            backtest_engine = BacktestEngine(initial_capital=initial_capital)
            results = backtest_engine.run(df_with_signals)

            # DB에 저장
            self.save_to_db(strategy_type, strategy_instance, kr_stock, us_stock, results, df_with_signals)

            # 결과 출력
            self.stdout.write(
                self.style.SUCCESS(
                    f"[{idx}] {stock_name} ({stock_code}): "
                    f"수익률 {results['total_return']:+.2f}%, "
                    f"거래 {results['total_trades']}회, "
                    f"승률 {results['win_rate']:.1f}%"
                )
            )

            return 'success'

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"[{idx}] {stock_name} ({stock_code}): 실패 - {str(e)}")
            )
            return 'fail'

    def get_price_data(self, kr_stock, us_stock, start_date, end_date):
        """가격 데이터 조회"""
        if kr_stock:
            price_data = PriceData.objects.filter(
                stock=kr_stock,
                date__range=[start_date, end_date]
            ).order_by('date').values(
                'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
            )

            df = pd.DataFrame(list(price_data))
            if not df.empty:
                df.rename(columns={
                    'open_price': 'open',
                    'high_price': 'high',
                    'low_price': 'low',
                    'close_price': 'close'
                }, inplace=True)
                # Decimal을 float로 변환
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = df[col].astype(float)

        else:  # us_stock
            price_data = USPriceData.objects.filter(
                stock=us_stock,
                date__range=[start_date, end_date]
            ).order_by('date').values(
                'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
            )

            df = pd.DataFrame(list(price_data))
            if not df.empty:
                df.rename(columns={
                    'open_price': 'open',
                    'high_price': 'high',
                    'low_price': 'low',
                    'close_price': 'close'
                }, inplace=True)
                # Decimal을 float로 변환
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = df[col].astype(float)

        return df

    def get_strategy(self, strategy_type):
        """전략 인스턴스 생성"""
        if strategy_type == 'ma_cross':
            return MovingAverageCrossStrategy()
        elif strategy_type == 'rsi':
            return RSIStrategy()
        elif strategy_type == 'bollinger':
            return BollingerBandsStrategy()
        elif strategy_type == 'squeeze_momentum':
            return SqueezeMomentumStrategy()
        else:
            return None

    def save_to_db(self, strategy_type, strategy_instance, kr_stock, us_stock, results, df_with_signals):
        """백테스트 결과를 DB에 저장"""
        # Strategy 객체 생성 또는 조회
        strategy, created = Strategy.objects.get_or_create(
            name=strategy_instance.get_name(),
            strategy_type=strategy_type,
            defaults={
                'parameters': strategy_instance.get_parameters(),
                'description': f'{strategy_instance.get_name()} 전략'
            }
        )

        # Backtest 객체 생성
        backtest = Backtest.objects.create(
            strategy=strategy,
            kr_stock=kr_stock,
            us_stock=us_stock,
            start_date=results['start_date'],
            end_date=results['end_date'],
            total_return=Decimal(str(round(results['total_return'], 2))),
            annual_return=Decimal(str(round(results['annual_return'], 2))),
            sharpe_ratio=Decimal(str(round(results['sharpe_ratio'], 4))) if results['sharpe_ratio'] else None,
            max_drawdown=Decimal(str(round(results['max_drawdown'], 2))),
            win_rate=Decimal(str(round(results['win_rate'], 2))),
            total_trades=results['total_trades'],
            initial_capital=Decimal(str(results['initial_capital'])),
            final_capital=Decimal(str(results['final_capital']))
        )

        # Signal 객체 생성 (너무 많으면 성능 문제가 있을 수 있으므로 옵션으로)
        # for trade in results['trades']:
        #     Signal.objects.create(
        #         backtest=backtest,
        #         date=trade['date'],
        #         signal_type='buy' if trade['type'] == 'buy' else 'sell',
        #         price=Decimal(str(trade['price'])),
        #         quantity=trade['quantity'],
        #         reason=f"{strategy_instance.get_name()} 신호"
        #     )

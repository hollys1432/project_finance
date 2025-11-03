"""
백테스트 결과 조회 및 분석 커맨드
"""
from django.core.management.base import BaseCommand
from quant.models import Strategy, Backtest
from django.db.models import Avg, Max, Min, Count


class Command(BaseCommand):
    help = '백테스트 결과 조회 및 분석'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strategy',
            type=str,
            help='전략 유형 필터 (ma_cross, rsi, bollinger)'
        )
        parser.add_argument(
            '--market',
            type=str,
            choices=['kr', 'us'],
            help='시장 필터 (kr: 한국, us: 미국)'
        )
        parser.add_argument(
            '--top',
            type=int,
            default=20,
            help='상위 N개 종목만 표시 (기본값: 20)'
        )
        parser.add_argument(
            '--min-return',
            type=float,
            help='최소 수익률 필터 (%)'
        )
        parser.add_argument(
            '--sort-by',
            type=str,
            default='total_return',
            choices=['total_return', 'sharpe_ratio', 'win_rate', 'total_trades'],
            help='정렬 기준 (기본값: total_return)'
        )

    def handle(self, *args, **options):
        strategy_type = options.get('strategy')
        market = options.get('market')
        top = options['top']
        min_return = options.get('min_return')
        sort_by = options['sort_by']

        # 쿼리 빌드
        backtests = Backtest.objects.all()

        if strategy_type:
            backtests = backtests.filter(strategy__strategy_type=strategy_type)

        if market == 'kr':
            backtests = backtests.filter(kr_stock__isnull=False)
        elif market == 'us':
            backtests = backtests.filter(us_stock__isnull=False)

        if min_return is not None:
            backtests = backtests.filter(total_return__gte=min_return)

        # 정렬
        backtests = backtests.order_by(f'-{sort_by}')[:top]

        # 통계 계산
        if backtests.exists():
            stats = backtests.aggregate(
                avg_return=Avg('total_return'),
                max_return=Max('total_return'),
                min_return=Min('total_return'),
                avg_sharpe=Avg('sharpe_ratio'),
                avg_win_rate=Avg('win_rate'),
                total_count=Count('id')
            )

            self.stdout.write(self.style.SUCCESS(f"\n{'='*100}"))
            self.stdout.write(self.style.SUCCESS("백테스트 결과 요약"))
            self.stdout.write(self.style.SUCCESS(f"{'='*100}"))

            if strategy_type:
                self.stdout.write(f"전략: {strategy_type}")
            if market:
                self.stdout.write(f"시장: {market}")

            self.stdout.write(f"\n총 백테스트 수: {stats['total_count']}개")
            self.stdout.write(f"평균 수익률: {stats['avg_return']:.2f}%")
            self.stdout.write(f"최고 수익률: {stats['max_return']:.2f}%")
            self.stdout.write(f"최저 수익률: {stats['min_return']:.2f}%")
            self.stdout.write(f"평균 샤프 비율: {stats['avg_sharpe']:.4f}" if stats['avg_sharpe'] else "평균 샤프 비율: N/A")
            self.stdout.write(f"평균 승률: {stats['avg_win_rate']:.2f}%")

            self.stdout.write(self.style.SUCCESS(f"\n{'='*100}"))
            self.stdout.write(self.style.SUCCESS(f"상위 {top}개 종목 (정렬 기준: {sort_by})"))
            self.stdout.write(self.style.SUCCESS(f"{'='*100}"))

            # 테이블 헤더
            header = f"{'순위':<5} {'종목명':<20} {'코드':<10} {'전략':<15} {'수익률':<10} {'샤프비율':<10} {'승률':<8} {'거래횟수':<8}"
            self.stdout.write(header)
            self.stdout.write("-" * 100)

            # 결과 출력
            for idx, bt in enumerate(backtests, 1):
                stock_name = bt.kr_stock.company_name if bt.kr_stock else bt.us_stock.company_name
                stock_code = bt.kr_stock.company_code if bt.kr_stock else bt.us_stock.symbol
                strategy_name = bt.strategy.get_strategy_type_display()

                # 수익률에 따라 색상 지정
                return_str = f"{bt.total_return:+.2f}%"
                if bt.total_return > 0:
                    return_colored = self.style.SUCCESS(return_str)
                elif bt.total_return < 0:
                    return_colored = self.style.ERROR(return_str)
                else:
                    return_colored = return_str

                sharpe_str = f"{bt.sharpe_ratio:.4f}" if bt.sharpe_ratio else "N/A"

                row = f"{idx:<5} {stock_name:<20} {stock_code:<10} {strategy_name:<15} {return_str:<10} {sharpe_str:<10} {bt.win_rate:.1f}%   {bt.total_trades:<8}"

                # 전체 행을 색상 처리
                if bt.total_return > 0:
                    self.stdout.write(self.style.SUCCESS(row))
                elif bt.total_return < 0:
                    self.stdout.write(self.style.ERROR(row))
                else:
                    self.stdout.write(row)

            self.stdout.write(self.style.SUCCESS(f"{'='*100}\n"))

        else:
            self.stdout.write(self.style.WARNING("백테스트 결과가 없습니다."))
            self.stdout.write("먼저 'python manage.py run_backtest_all' 명령어로 백테스트를 실행해주세요.")

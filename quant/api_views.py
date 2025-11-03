"""
퀀트 전략 API Views
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from stocks.models import CompanyInfo, PriceData, USCompanyInfo, USPriceData
from .models import Strategy, Backtest, Signal
from .strategies.ma_cross import MovingAverageCrossStrategy
from .strategies.rsi_strategy import RSIStrategy
from .strategies.bollinger_strategy import BollingerBandsStrategy
from .strategies.squeeze_momentum_strategy import SqueezeMomentumStrategy
from datetime import datetime, timedelta
import pandas as pd
from decimal import Decimal


@require_GET
def get_strategy_signals(request, company_id):
    """
    특정 종목의 전략 신호 조회 (한국 주식)

    Query Parameters:
        - strategy: 전략 유형 (ma_cross, rsi, bollinger, squeeze_momentum) 기본값: ma_cross
        - period: 기간 (1D, 1W, 1M) 기본값: 1D
    """
    try:
        # stocks.api_views의 리샘플링 함수 가져오기
        from stocks.api_views import resample_price_data

        company = CompanyInfo.objects.get(id=company_id)
        strategy_type = request.GET.get('strategy', 'ma_cross')
        period = request.GET.get('period', '1D')

        # 최근 데이터 조회
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=3650)  # 10년

        # 가격 데이터 조회
        price_data = PriceData.objects.filter(
            stock=company,
            date__gte=start_date
        ).order_by('date').values(
            'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
        )

        if not price_data.exists():
            return JsonResponse({'error': '가격 데이터가 없습니다.'}, status=404)

        # DataFrame 생성
        df_data = []
        for data in price_data:
            df_data.append({
                'date': data['date'],
                'open': float(data['open_price']) if data['open_price'] else float(data['close_price']),
                'high': float(data['high_price']) if data['high_price'] else float(data['close_price']),
                'low': float(data['low_price']) if data['low_price'] else float(data['close_price']),
                'close': float(data['close_price']),
                'volume': int(data['volume']) if data['volume'] else 0
            })

        df = pd.DataFrame(df_data)

        # 주봉/월봉 리샘플링 (차트와 동일한 데이터 사용)
        df = resample_price_data(df, period)

        # 전략 선택
        strategy = get_strategy_instance(strategy_type)
        if not strategy:
            return JsonResponse({'error': '잘못된 전략 유형입니다.'}, status=400)

        # 신호 생성
        df_with_signals = strategy.generate_signals(df)

        # 매수/매도 신호 추출
        buy_signals = []
        sell_signals = []

        for idx, row in df_with_signals.iterrows():
            if row['signal'] == 1:  # 매수
                buy_signals.append({
                    'time': row['date'].strftime('%Y-%m-%d'),
                    'position': 'belowBar',
                    'color': '#26a69a',  # 녹색 (매수)
                    'shape': 'arrowDown',
                    'text': 'BUY'
                })
            elif row['signal'] == -1:  # 매도
                sell_signals.append({
                    'time': row['date'].strftime('%Y-%m-%d'),
                    'position': 'belowBar',
                    'color': '#ef5350',  # 빨간색 (매도)
                    'shape': 'arrowDown',
                    'text': 'SELL'
                })

        # 스퀴즈 모멘텀 전략의 경우 지표 데이터 추가
        indicators = {}
        if strategy_type == 'squeeze_momentum':
            # 볼린저 밴드
            if 'bb_upper' in df_with_signals.columns:
                indicators['bb_upper'] = [
                    {'time': row['date'].strftime('%Y-%m-%d'), 'value': float(row['bb_upper'])}
                    for _, row in df_with_signals.iterrows() if pd.notna(row['bb_upper'])
                ]
            if 'bb_lower' in df_with_signals.columns:
                indicators['bb_lower'] = [
                    {'time': row['date'].strftime('%Y-%m-%d'), 'value': float(row['bb_lower'])}
                    for _, row in df_with_signals.iterrows() if pd.notna(row['bb_lower'])
                ]

            # 켈트너 채널
            if 'kc_upper' in df_with_signals.columns:
                indicators['kc_upper'] = [
                    {'time': row['date'].strftime('%Y-%m-%d'), 'value': float(row['kc_upper'])}
                    for _, row in df_with_signals.iterrows() if pd.notna(row['kc_upper'])
                ]
            if 'kc_lower' in df_with_signals.columns:
                indicators['kc_lower'] = [
                    {'time': row['date'].strftime('%Y-%m-%d'), 'value': float(row['kc_lower'])}
                    for _, row in df_with_signals.iterrows() if pd.notna(row['kc_lower'])
                ]

            # EMA
            if 'ema' in df_with_signals.columns:
                indicators['ema'] = [
                    {'time': row['date'].strftime('%Y-%m-%d'), 'value': float(row['ema'])}
                    for _, row in df_with_signals.iterrows() if pd.notna(row['ema'])
                ]

        response_data = {
            'strategy_name': strategy.get_name(),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'total_signals': len(buy_signals) + len(sell_signals)
        }

        if indicators:
            response_data['indicators'] = indicators

        return JsonResponse(response_data)

    except CompanyInfo.DoesNotExist:
        return JsonResponse({'error': '종목을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'오류: {str(e)}'}, status=500)


@require_GET
def get_us_strategy_signals(request, company_id):
    """
    특정 종목의 전략 신호 조회 (미국 주식)

    Query Parameters:
        - strategy: 전략 유형 (ma_cross, rsi, bollinger, squeeze_momentum) 기본값: ma_cross
        - period: 기간 (1D, 1W, 1M) 기본값: 1D
    """
    try:
        # stocks.api_views의 리샘플링 함수 가져오기
        from stocks.api_views import resample_price_data

        company = USCompanyInfo.objects.get(id=company_id)
        strategy_type = request.GET.get('strategy', 'ma_cross')
        period = request.GET.get('period', '1D')

        # 최근 데이터 조회
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=3650)  # 10년

        # 가격 데이터 조회
        price_data = USPriceData.objects.filter(
            stock=company,
            date__gte=start_date
        ).order_by('date').values(
            'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
        )

        if not price_data.exists():
            return JsonResponse({'error': '가격 데이터가 없습니다.'}, status=404)

        # DataFrame 생성
        df_data = []
        for data in price_data:
            df_data.append({
                'date': data['date'],
                'open': float(data['open_price']) if data['open_price'] else float(data['close_price']),
                'high': float(data['high_price']) if data['high_price'] else float(data['close_price']),
                'low': float(data['low_price']) if data['low_price'] else float(data['close_price']),
                'close': float(data['close_price']),
                'volume': int(data['volume']) if data['volume'] else 0
            })

        df = pd.DataFrame(df_data)

        # 주봉/월봉 리샘플링 (차트와 동일한 데이터 사용)
        df = resample_price_data(df, period)

        # 전략 선택
        strategy = get_strategy_instance(strategy_type)
        if not strategy:
            return JsonResponse({'error': '잘못된 전략 유형입니다.'}, status=400)

        # 신호 생성
        df_with_signals = strategy.generate_signals(df)

        # 매수/매도 신호 추출
        buy_signals = []
        sell_signals = []

        for idx, row in df_with_signals.iterrows():
            if row['signal'] == 1:  # 매수
                buy_signals.append({
                    'time': row['date'].strftime('%Y-%m-%d'),
                    'position': 'belowBar',
                    'color': '#26a69a',  # 녹색 (매수)
                    'shape': 'arrowDown',
                    'text': 'BUY'
                })
            elif row['signal'] == -1:  # 매도
                sell_signals.append({
                    'time': row['date'].strftime('%Y-%m-%d'),
                    'position': 'belowBar',
                    'color': '#ef5350',  # 빨간색 (매도)
                    'shape': 'arrowDown',
                    'text': 'SELL'
                })

        # 스퀴즈 모멘텀 전략의 경우 지표 데이터 추가
        indicators = {}
        if strategy_type == 'squeeze_momentum':
            # 볼린저 밴드
            if 'bb_upper' in df_with_signals.columns:
                indicators['bb_upper'] = [
                    {'time': row['date'].strftime('%Y-%m-%d'), 'value': float(row['bb_upper'])}
                    for _, row in df_with_signals.iterrows() if pd.notna(row['bb_upper'])
                ]
            if 'bb_lower' in df_with_signals.columns:
                indicators['bb_lower'] = [
                    {'time': row['date'].strftime('%Y-%m-%d'), 'value': float(row['bb_lower'])}
                    for _, row in df_with_signals.iterrows() if pd.notna(row['bb_lower'])
                ]

            # 켈트너 채널
            if 'kc_upper' in df_with_signals.columns:
                indicators['kc_upper'] = [
                    {'time': row['date'].strftime('%Y-%m-%d'), 'value': float(row['kc_upper'])}
                    for _, row in df_with_signals.iterrows() if pd.notna(row['kc_upper'])
                ]
            if 'kc_lower' in df_with_signals.columns:
                indicators['kc_lower'] = [
                    {'time': row['date'].strftime('%Y-%m-%d'), 'value': float(row['kc_lower'])}
                    for _, row in df_with_signals.iterrows() if pd.notna(row['kc_lower'])
                ]

            # EMA
            if 'ema' in df_with_signals.columns:
                indicators['ema'] = [
                    {'time': row['date'].strftime('%Y-%m-%d'), 'value': float(row['ema'])}
                    for _, row in df_with_signals.iterrows() if pd.notna(row['ema'])
                ]

        response_data = {
            'strategy_name': strategy.get_name(),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'total_signals': len(buy_signals) + len(sell_signals)
        }

        if indicators:
            response_data['indicators'] = indicators

        return JsonResponse(response_data)

    except USCompanyInfo.DoesNotExist:
        return JsonResponse({'error': '종목을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'오류: {str(e)}'}, status=500)


@require_GET
def get_backtest_results(request, company_id):
    """특정 종목의 백테스트 결과 목록 조회"""
    try:
        # 한국 주식
        kr_backtests = Backtest.objects.filter(
            kr_stock_id=company_id
        ).select_related('strategy').order_by('-created_at')[:10]

        # 미국 주식
        us_backtests = Backtest.objects.filter(
            us_stock_id=company_id
        ).select_related('strategy').order_by('-created_at')[:10]

        backtests = list(kr_backtests) + list(us_backtests)
        backtests.sort(key=lambda x: x.created_at, reverse=True)

        results = []
        for bt in backtests[:10]:
            results.append({
                'id': bt.id,
                'strategy_name': bt.strategy.name,
                'strategy_type': bt.strategy.get_strategy_type_display(),
                'start_date': bt.start_date.isoformat(),
                'end_date': bt.end_date.isoformat(),
                'total_return': float(bt.total_return),
                'annual_return': float(bt.annual_return),
                'sharpe_ratio': float(bt.sharpe_ratio) if bt.sharpe_ratio else None,
                'max_drawdown': float(bt.max_drawdown),
                'win_rate': float(bt.win_rate),
                'total_trades': bt.total_trades,
                'created_at': bt.created_at.isoformat()
            })

        return JsonResponse({'results': results})

    except Exception as e:
        return JsonResponse({'error': f'오류: {str(e)}'}, status=500)


@require_GET
def get_backtest_detail(request, backtest_id):
    """백테스트 상세 결과 조회 (신호 포함)"""
    try:
        backtest = Backtest.objects.get(id=backtest_id)

        # 신호 조회
        signals = Signal.objects.filter(backtest=backtest).order_by('date')

        buy_signals = []
        sell_signals = []

        for signal in signals:
            signal_data = {
                'time': signal.date.strftime('%Y-%m-%d'),
                'price': float(signal.price),
                'quantity': signal.quantity
            }

            if signal.signal_type == 'buy':
                buy_signals.append({
                    **signal_data,
                    'position': 'belowBar',
                    'color': '#2196F3',
                    'shape': 'arrowUp',
                    'text': 'B'
                })
            else:  # sell
                sell_signals.append({
                    **signal_data,
                    'position': 'aboveBar',
                    'color': '#e91e63',
                    'shape': 'arrowDown',
                    'text': 'S'
                })

        return JsonResponse({
            'backtest_id': backtest.id,
            'strategy_name': backtest.strategy.name,
            'total_return': float(backtest.total_return),
            'annual_return': float(backtest.annual_return),
            'sharpe_ratio': float(backtest.sharpe_ratio) if backtest.sharpe_ratio else None,
            'max_drawdown': float(backtest.max_drawdown),
            'win_rate': float(backtest.win_rate),
            'total_trades': backtest.total_trades,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals
        })

    except Backtest.DoesNotExist:
        return JsonResponse({'error': '백테스트 결과를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'오류: {str(e)}'}, status=500)


def get_strategy_instance(strategy_type):
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

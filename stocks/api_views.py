# stocks/api_views.py

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Q, Max, Min
from datetime import datetime, timedelta
import json
import pandas as pd
from decimal import Decimal
from .models import CompanyInfo, PriceData, USCompanyInfo, USPriceData
from quant.indicators import calculate_bollinger_bands

class DecimalEncoder(json.JSONEncoder):
    """Decimal 타입을 JSON으로 변환하기 위한 인코더"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def resample_price_data(df, period):
    """
    pandas를 사용하여 가격 데이터를 주봉/월봉으로 리샘플링
    
    Args:
        df: pandas DataFrame with OHLCV data
        period: '1D' (일봉), '1W' (주봉), '1M' (월봉)
    
    Returns:
        resampled DataFrame
    """
    if df.empty:
        return df
    
    # 날짜를 인덱스로 설정
    df = df.set_index('date')
    df.index = pd.to_datetime(df.index)
    
    if period == '1D':
        # 일봉은 그대로 반환
        return df.reset_index()
    elif period == '1W':
        # 주봉 - 일요일 시작 기준으로 리샘플링 (일반적인 금융 플랫폼 기준)
        # W 또는 W-SUN: 일요일에 끝나는 주 (월~일)
        # label='left': 주의 시작일을 레이블로 사용
        # closed='left': 왼쪽 경계 포함
        resampled = df.resample('W', label='left', closed='left').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    elif period == '1M':
        # 월봉 - 월 시작일 기준으로 리샘플링
        resampled = df.resample('MS').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    else:
        # 기본값은 일봉
        return df.reset_index()
    
    return resampled.reset_index()


@require_GET
def search_companies(request):
    """통합 회사 검색 API (한국 + 미국)"""
    query = request.GET.get('q', '').strip()
    market = request.GET.get('market', 'all')  # all, kr, us
    
    if not query:
        return JsonResponse({'results': []})
    
    results = []
    
    # 한국 주식 검색
    if market in ['all', 'kr']:
        kr_companies = CompanyInfo.objects.filter(
            Q(company_name__icontains=query) | 
            Q(company_code__icontains=query),
            is_active=True
        )[:10]  # 최대 10개 결과
        
        for company in kr_companies:
            # 최신 가격 정보 가져오기
            latest_price = PriceData.objects.filter(
                stock=company
            ).order_by('-date').first()
            
            results.append({
                'id': company.id,
                'code': company.company_code,
                'name': company.company_name,
                'market': company.market or 'N/A',
                'type': 'kr',  # 한국 주식 표시
                'latest_price': float(latest_price.close_price) if latest_price else None,
                'latest_date': latest_price.date.isoformat() if latest_price else None
            })
    
    # 미국 주식 검색
    if market in ['all', 'us']:
        us_companies = USCompanyInfo.objects.filter(
            Q(company_name__icontains=query) | 
            Q(symbol__icontains=query),
            is_active=True
        )[:10]  # 최대 10개 결과
        
        for company in us_companies:
            # 최신 가격 정보 가져오기
            latest_price = USPriceData.objects.filter(
                stock=company
            ).order_by('-date').first()
            
            results.append({
                'id': company.id,
                'symbol': company.symbol,
                'name': company.company_name,
                'exchange': company.exchange or 'N/A',
                'sector': company.sector or 'N/A',
                'type': 'us',  # 미국 주식 표시
                'latest_price': float(latest_price.close_price) if latest_price else None,
                'latest_date': latest_price.date.isoformat() if latest_price else None,
                'currency': company.currency or 'USD'
            })
    
    # 결과 제한 (총 20개)
    return JsonResponse({'results': results[:20]})


@require_GET
def get_company_data(request, company_id):
    """한국 회사 상세 데이터 API - 주봉/월봉 지원"""
    try:
        company = CompanyInfo.objects.get(id=company_id)
        
        # 기간 파라미터
        period = request.GET.get('period', '1D')  # 1D, 1W, 1M
        
        # 전체 데이터 조회 (기간별로 필요한 만큼만)
        if period == '1D':
            # 일봉 - 최근 2년
            start_date = datetime.now().date() - timedelta(days=3650)
        elif period == '1W':
            # 주봉 - 최근 5년
            start_date = datetime.now().date() - timedelta(days=3650)
        elif period == '1M':
            # 월봉 - 최근 10년
            start_date = datetime.now().date() - timedelta(days=3650)
        else:
            # 기본값
            start_date = datetime.now().date() - timedelta(days=3650)
        
        # 가격 데이터 조회
        price_data = PriceData.objects.filter(
            stock=company,
            date__gte=start_date
        ).order_by('date').values(
            'date', 'open_price', 'high_price', 
            'low_price', 'close_price', 'volume'
        )
        
        if not price_data.exists():
            return JsonResponse({
                'error': '해당 기간의 데이터가 없습니다.'
            }, status=404)
        
        # pandas DataFrame 생성
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
        
        if df.empty:
            return JsonResponse({
                'error': '데이터 처리 중 오류가 발생했습니다.'
            }, status=500)
        
        # 주봉/월봉 리샘플링
        resampled_df = resample_price_data(df, period)
        
        # 차트 데이터 준비
        labels = []
        ohlc_data = []
        volumes = []
        prices = []  # MDD 계산용

        # 이동평균 계산을 위한 DataFrame 준비
        resampled_df['ma5'] = resampled_df['close'].rolling(window=5, min_periods=5).mean()
        resampled_df['ma20'] = resampled_df['close'].rolling(window=20, min_periods=20).mean()
        resampled_df['ma60'] = resampled_df['close'].rolling(window=60, min_periods=60).mean()
        resampled_df['ma120'] = resampled_df['close'].rolling(window=120, min_periods=120).mean()
        resampled_df['ma240'] = resampled_df['close'].rolling(window=240, min_periods=240).mean()

        # 볼린저 밴드 계산 (20일, 2 표준편차)
        bb = calculate_bollinger_bands(resampled_df['close'], period=20, std_dev=2)
        resampled_df['bb_upper'] = bb['upper']
        resampled_df['bb_middle'] = bb['middle']
        resampled_df['bb_lower'] = bb['lower']

        ma5_data = []
        ma20_data = []
        ma60_data = []
        ma120_data = []
        ma240_data = []
        bb_upper_data = []
        bb_middle_data = []
        bb_lower_data = []

        for _, row in resampled_df.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])
            labels.append(date_str)
            
            ohlc_data.append({
                'time': date_str,
                'open': round(row['open'], 2),
                'high': round(row['high'], 2),
                'low': round(row['low'], 2),
                'close': round(row['close'], 2)
            })
            
            volumes.append({
                'time': date_str,
                'value': int(row['volume']),
                'color': 'rgba(38, 166, 154, 0.6)' if row['close'] >= row['open'] else 'rgba(239, 83, 80, 0.6)'
            })

            prices.append(row['close'])

            # 이동평균 데이터 추가
            if not pd.isna(row['ma5']):
                ma5_data.append({
                    'time': date_str,
                    'value': round(row['ma5'], 2)
                })

            if not pd.isna(row['ma20']):
                ma20_data.append({
                    'time': date_str,
                    'value': round(row['ma20'], 2)
                })

            if not pd.isna(row['ma60']):
                ma60_data.append({
                    'time': date_str,
                    'value': round(row['ma60'], 2)
                })

            if not pd.isna(row['ma120']):
                ma120_data.append({
                    'time': date_str,
                    'value': round(row['ma120'], 2)
                })

            if not pd.isna(row['ma240']):
                ma240_data.append({
                    'time': date_str,
                    'value': round(row['ma240'], 2)
                })

            # 볼린저 밴드 데이터 추가
            if not pd.isna(row['bb_upper']):
                bb_upper_data.append({
                    'time': date_str,
                    'value': round(row['bb_upper'], 2)
                })

            if not pd.isna(row['bb_middle']):
                bb_middle_data.append({
                    'time': date_str,
                    'value': round(row['bb_middle'], 2)
                })

            if not pd.isna(row['bb_lower']):
                bb_lower_data.append({
                    'time': date_str,
                    'value': round(row['bb_lower'], 2)
                })

        # MDD 계산
        mdd_data = calculate_mdd(prices)
        
        # 통계 정보
        stats = {
            'current_price': prices[-1] if prices else 0,
            'max_price': max(prices) if prices else 0,
            'min_price': min(prices) if prices else 0,
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'price_change': prices[-1] - prices[0] if len(prices) >= 2 else 0,
            'price_change_rate': ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) >= 2 and prices[0] != 0 else 0,
            'avg_volume': sum([v['value'] for v in volumes]) / len(volumes) if volumes else 0,
            'max_volume': max([v['value'] for v in volumes]) if volumes else 0,
            'min_volume': min([v['value'] for v in volumes]) if volumes else 0,
            'data_count': len(prices)
        }
        
        response_data = {
            'company': {
                'id': company.id,
                'code': company.company_code,
                'name': company.company_name,
                'market': company.market or 'N/A'
            },
            'chart_data': {
                'labels': labels,
                'ohlc': ohlc_data,
                'volumes': volumes,
                'ma5': ma5_data,
                'ma20': ma20_data,
                'ma60': ma60_data,
                'ma120': ma120_data,
                'ma240': ma240_data,
                'bb_upper': bb_upper_data,
                'bb_middle': bb_middle_data,
                'bb_lower': bb_lower_data,
                'period': period
            },
            'mdd_data': mdd_data,
            'stats': stats,
            'period_info': {
                'start': start_date.isoformat(),
                'end': datetime.now().date().isoformat(),
                'period': period,
                'total_points': len(prices)
            }
        }
        
        return JsonResponse(response_data, encoder=DecimalEncoder)
        
    except CompanyInfo.DoesNotExist:
        return JsonResponse({'error': '회사를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'데이터 처리 중 오류: {str(e)}'}, status=500)


@require_GET
def get_us_company_data(request, company_id):
    """미국 회사 상세 데이터 API - 주봉/월봉 지원"""
    try:
        company = USCompanyInfo.objects.get(id=company_id)
        
        # 기간 파라미터
        period = request.GET.get('period', '1D')  # 1D, 1W, 1M
        
        # 전체 데이터 조회 (기간별로 필요한 만큼만)
        if period == '1D':
            # 일봉 - 최근 2년
            start_date = datetime.now().date() - timedelta(days=3650)
        elif period == '1W':
            # 주봉 - 최근 5년
            start_date = datetime.now().date() - timedelta(days=3650)
        elif period == '1M':
            # 월봉 - 최근 10년
            start_date = datetime.now().date() - timedelta(days=3650)
        else:
            # 기본값
            start_date = datetime.now().date() - timedelta(days=3650)
        
        # 가격 데이터 조회
        price_data = USPriceData.objects.filter(
            stock=company,
            date__gte=start_date
        ).order_by('date').values(
            'date', 'open_price', 'high_price', 
            'low_price', 'close_price', 'adj_close_price', 'volume'
        )
        
        if not price_data.exists():
            return JsonResponse({
                'error': '해당 기간의 데이터가 없습니다.'
            }, status=404)
        
        # pandas DataFrame 생성
        df_data = []
        for data in price_data:
            df_data.append({
                'date': data['date'],
                'open': float(data['open_price']) if data['open_price'] else float(data['close_price']),
                'high': float(data['high_price']) if data['high_price'] else float(data['close_price']),
                'low': float(data['low_price']) if data['low_price'] else float(data['close_price']),
                'close': float(data['close_price']) if data['close_price'] else 0,
                'adj_close': float(data['adj_close_price']) if data['adj_close_price'] else float(data['close_price']),
                'volume': int(data['volume']) if data['volume'] else 0
            })
        
        df = pd.DataFrame(df_data)
        
        if df.empty:
            return JsonResponse({
                'error': '데이터 처리 중 오류가 발생했습니다.'
            }, status=500)
        
        # 주봉/월봉 리샘플링 (조정종가 포함)
        if period == '1D':
            resampled_df = df.copy()
        else:
            df_temp = df.set_index('date')
            df_temp.index = pd.to_datetime(df_temp.index)
            
            if period == '1W':
                # 주봉 - 일요일 시작 기준으로 리샘플링 (일반적인 금융 플랫폼 기준)
                resampled = df_temp.resample('W', label='left', closed='left').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'adj_close': 'last',
                    'volume': 'sum'
                }).dropna()
            elif period == '1M':
                resampled = df_temp.resample('MS').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'adj_close': 'last',
                    'volume': 'sum'
                }).dropna()
            
            resampled_df = resampled.reset_index()
        
        # 차트 데이터 준비
        labels = []
        ohlc_data = []
        volumes = []
        prices = []  # MDD 계산용 (조정종가 기준)

        # 이동평균 계산을 위한 DataFrame 준비
        resampled_df['ma5'] = resampled_df['close'].rolling(window=5, min_periods=5).mean()
        resampled_df['ma20'] = resampled_df['close'].rolling(window=20, min_periods=20).mean()
        resampled_df['ma60'] = resampled_df['close'].rolling(window=60, min_periods=60).mean()
        resampled_df['ma120'] = resampled_df['close'].rolling(window=120, min_periods=120).mean()
        resampled_df['ma240'] = resampled_df['close'].rolling(window=240, min_periods=240).mean()

        # 볼린저 밴드 계산 (20일, 2 표준편차)
        bb = calculate_bollinger_bands(resampled_df['close'], period=20, std_dev=2)
        resampled_df['bb_upper'] = bb['upper']
        resampled_df['bb_middle'] = bb['middle']
        resampled_df['bb_lower'] = bb['lower']

        ma5_data = []
        ma20_data = []
        ma60_data = []
        ma120_data = []
        ma240_data = []
        bb_upper_data = []
        bb_middle_data = []
        bb_lower_data = []

        for _, row in resampled_df.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])
            labels.append(date_str)
            
            ohlc_data.append({
                'time': date_str,
                'open': round(row['open'], 2),
                'high': round(row['high'], 2),
                'low': round(row['low'], 2),
                'close': round(row['close'], 2)
            })
            
            volumes.append({
                'time': date_str,
                'value': int(row['volume']),
                'color': 'rgba(38, 166, 154, 0.6)' if row['close'] >= row['open'] else 'rgba(239, 83, 80, 0.6)'
            })

            prices.append(row['adj_close'])  # 조정종가 기준 MDD

            # 이동평균 데이터 추가
            if not pd.isna(row['ma5']):
                ma5_data.append({
                    'time': date_str,
                    'value': round(row['ma5'], 2)
                })

            if not pd.isna(row['ma20']):
                ma20_data.append({
                    'time': date_str,
                    'value': round(row['ma20'], 2)
                })

            if not pd.isna(row['ma60']):
                ma60_data.append({
                    'time': date_str,
                    'value': round(row['ma60'], 2)
                })

            if not pd.isna(row['ma120']):
                ma120_data.append({
                    'time': date_str,
                    'value': round(row['ma120'], 2)
                })

            if not pd.isna(row['ma240']):
                ma240_data.append({
                    'time': date_str,
                    'value': round(row['ma240'], 2)
                })

            # 볼린저 밴드 데이터 추가
            if not pd.isna(row['bb_upper']):
                bb_upper_data.append({
                    'time': date_str,
                    'value': round(row['bb_upper'], 2)
                })

            if not pd.isna(row['bb_middle']):
                bb_middle_data.append({
                    'time': date_str,
                    'value': round(row['bb_middle'], 2)
                })

            if not pd.isna(row['bb_lower']):
                bb_lower_data.append({
                    'time': date_str,
                    'value': round(row['bb_lower'], 2)
                })

        # MDD 계산 (조정종가 기준)
        mdd_data = calculate_mdd(prices)
        
        # 통계 정보
        stats = {
            'current_price': resampled_df.iloc[-1]['close'] if len(resampled_df) > 0 else 0,
            'adj_close_price': resampled_df.iloc[-1]['adj_close'] if len(resampled_df) > 0 else 0,
            'max_price': resampled_df['close'].max() if len(resampled_df) > 0 else 0,
            'min_price': resampled_df['close'].min() if len(resampled_df) > 0 else 0,
            'avg_price': resampled_df['close'].mean() if len(resampled_df) > 0 else 0,
            'price_change': (resampled_df.iloc[-1]['close'] - resampled_df.iloc[0]['close']) if len(resampled_df) >= 2 else 0,
            'price_change_rate': ((resampled_df.iloc[-1]['close'] - resampled_df.iloc[0]['close']) / resampled_df.iloc[0]['close'] * 100) if len(resampled_df) >= 2 and resampled_df.iloc[0]['close'] != 0 else 0,
            'adj_price_change': (resampled_df.iloc[-1]['adj_close'] - resampled_df.iloc[0]['adj_close']) if len(resampled_df) >= 2 else 0,
            'adj_price_change_rate': ((resampled_df.iloc[-1]['adj_close'] - resampled_df.iloc[0]['adj_close']) / resampled_df.iloc[0]['adj_close'] * 100) if len(resampled_df) >= 2 and resampled_df.iloc[0]['adj_close'] != 0 else 0,
            'avg_volume': sum([v['value'] for v in volumes]) / len(volumes) if volumes else 0,
            'max_volume': max([v['value'] for v in volumes]) if volumes else 0,
            'min_volume': min([v['value'] for v in volumes]) if volumes else 0,
            'data_count': len(prices)
        }
        
        response_data = {
            'company': {
                'id': company.id,
                'symbol': company.symbol,
                'name': company.company_name,
                'exchange': company.exchange or 'N/A',
                'sector': company.sector or 'N/A',
                'industry': company.industry or 'N/A',
                'currency': company.currency or 'USD'
            },
            'chart_data': {
                'labels': labels,
                'ohlc': ohlc_data,
                'volumes': volumes,
                'ma5': ma5_data,
                'ma20': ma20_data,
                'ma60': ma60_data,
                'ma120': ma120_data,
                'ma240': ma240_data,
                'bb_upper': bb_upper_data,
                'bb_middle': bb_middle_data,
                'bb_lower': bb_lower_data,
                'period': period
            },
            'mdd_data': mdd_data,
            'stats': stats,
            'period_info': {
                'start': start_date.isoformat(),
                'end': datetime.now().date().isoformat(),
                'period': period,
                'total_points': len(prices)
            }
        }
        
        return JsonResponse(response_data, encoder=DecimalEncoder)
        
    except USCompanyInfo.DoesNotExist:
        return JsonResponse({'error': '회사를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'데이터 처리 중 오류: {str(e)}'}, status=500)


@require_GET 
def get_price_range(request, company_id):
    """특정 기간의 한국 주식 가격 데이터 조회 API"""
    try:
        company = CompanyInfo.objects.get(id=company_id)
        
        # 날짜 파라미터
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = datetime.now().date() - timedelta(days=30)
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = datetime.now().date()
        
        # 가격 데이터 조회
        price_data = PriceData.objects.filter(
            stock=company,
            date__range=[start_date, end_date]
        ).order_by('date').values(
            'date', 'open_price', 'high_price', 
            'low_price', 'close_price', 'volume'
        )
        
        # OHLC 데이터 포맷
        ohlc_data = []
        for data in price_data:
            ohlc_data.append({
                'date': data['date'].isoformat(),
                'open': float(data['open_price']) if data['open_price'] else float(data['close_price']),
                'high': float(data['high_price']) if data['high_price'] else float(data['close_price']),
                'low': float(data['low_price']) if data['low_price'] else float(data['close_price']),
                'close': float(data['close_price']),
                'volume': int(data['volume']) if data['volume'] else 0
            })
        
        return JsonResponse({
            'company_id': company_id,
            'data': ohlc_data,
            'count': len(ohlc_data)
        })
        
    except CompanyInfo.DoesNotExist:
        return JsonResponse({'error': '회사를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET 
def get_us_price_range(request, company_id):
    """특정 기간의 미국 주식 가격 데이터 조회 API"""
    try:
        company = USCompanyInfo.objects.get(id=company_id)
        
        # 날짜 파라미터
        start_date = request.GET.get('start')
        end_date = request.GET.get('end')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = datetime.now().date() - timedelta(days=30)
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end_date = datetime.now().date()
        
        # 가격 데이터 조회
        price_data = USPriceData.objects.filter(
            stock=company,
            date__range=[start_date, end_date]
        ).order_by('date').values(
            'date', 'open_price', 'high_price', 
            'low_price', 'close_price', 'adj_close_price', 'volume'
        )
        
        # OHLC 데이터 포맷
        ohlc_data = []
        for data in price_data:
            ohlc_data.append({
                'date': data['date'].isoformat(),
                'open': float(data['open_price']) if data['open_price'] else float(data['close_price']),
                'high': float(data['high_price']) if data['high_price'] else float(data['close_price']),
                'low': float(data['low_price']) if data['low_price'] else float(data['close_price']),
                'close': float(data['close_price']),
                'adj_close': float(data['adj_close_price']) if data['adj_close_price'] else float(data['close_price']),
                'volume': int(data['volume']) if data['volume'] else 0
            })
        
        return JsonResponse({
            'company_id': company_id,
            'data': ohlc_data,
            'count': len(ohlc_data),
            'currency': company.currency or 'USD'
        })
        
    except USCompanyInfo.DoesNotExist:
        return JsonResponse({'error': '회사를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def calculate_mdd(prices):
    """Maximum Drawdown 계산"""
    if not prices or len(prices) < 2:
        return {
            'mdd': 0,
            'mdd_data': [],
            'peak': 0,
            'trough': 0,
            'peak_index': 0,
            'trough_index': 0
        }
    
    max_price = prices[0]
    max_drawdown = 0
    mdd_peak = prices[0]
    mdd_trough = prices[0]
    mdd_data = []
    peak_index = 0
    trough_index = 0
    current_peak_index = 0
    
    for i, price in enumerate(prices):
        if price > max_price:
            max_price = price
            current_peak_index = i
        
        drawdown = ((max_price - price) / max_price) * 100 if max_price != 0 else 0
        mdd_data.append(-drawdown)  # 음수로 표시
        
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            mdd_peak = max_price
            mdd_trough = price
            peak_index = current_peak_index
            trough_index = i
    
    return {
        'mdd': max_drawdown,
        'mdd_data': mdd_data,
        'peak': mdd_peak,
        'trough': mdd_trough,
        'peak_index': peak_index,
        'trough_index': trough_index
    }
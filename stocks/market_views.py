"""
시장 지수 데이터 API 뷰
"""

from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import sys
import os

# market_data_fetcher 모듈 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from market_data_fetcher import MarketDataFetcher


class MarketDashboardView(TemplateView):
    """메인 시장 대시보드 페이지"""
    template_name = 'main.html'


class MarketDataAPIView:
    """시장 지수 데이터 API"""

    def __init__(self):
        self.fetcher = MarketDataFetcher()

    def get_all_indices(self, request):
        """모든 지수 데이터 반환"""
        try:
            period = request.GET.get('period', '1mo')
            data = self.fetcher.get_all_indices(period=period)

            return JsonResponse({
                'success': True,
                'data': data,
                'timestamp': data.get(list(data.keys())[0], {}).get('timestamp', '')
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def get_index_data(self, request, index_id):
        """특정 지수 데이터 반환"""
        try:
            period = request.GET.get('period', '1mo')

            # index_id로 심볼 찾기
            indices = self.fetcher.INDICES
            if index_id not in indices:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid index ID: {index_id}'
                }, status=404)

            symbol = indices[index_id]['symbol']
            data = self.fetcher.get_index_data(symbol, period=period)

            # 메타데이터 추가
            data['id'] = index_id
            data['name'] = indices[index_id]['name']
            data['badge'] = indices[index_id]['badge']

            return JsonResponse({
                'success': True,
                'data': data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def get_realtime_quotes(self, request):
        """모든 지수의 실시간 시세 반환 (빠른 조회)"""
        try:
            result = {}

            for index_id, index_info in self.fetcher.INDICES.items():
                symbol = index_info['symbol']
                quote = self.fetcher.get_realtime_quote(symbol)

                quote['id'] = index_id
                quote['name'] = index_info['name']
                quote['badge'] = index_info['badge']

                result[index_id] = quote

            return JsonResponse({
                'success': True,
                'data': result
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# 함수형 뷰로 래핑
market_api = MarketDataAPIView()


@csrf_exempt
def market_all_indices(request):
    """모든 지수 데이터"""
    return market_api.get_all_indices(request)


@csrf_exempt
def market_index_detail(request, index_id):
    """특정 지수 상세 데이터"""
    return market_api.get_index_data(request, index_id)


@csrf_exempt
def market_realtime_quotes(request):
    """실시간 시세"""
    return market_api.get_realtime_quotes(request)

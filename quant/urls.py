"""
Quant 앱 URL 설정
"""
from django.urls import path
from . import api_views

app_name = 'quant'

urlpatterns = [
    # 한국 주식 전략 신호 API
    path('api/kr/<int:company_id>/signals/', api_views.get_strategy_signals, name='kr_strategy_signals'),

    # 미국 주식 전략 신호 API
    path('api/us/<int:company_id>/signals/', api_views.get_us_strategy_signals, name='us_strategy_signals'),

    # 백테스트 결과 목록
    path('api/backtest/<int:company_id>/', api_views.get_backtest_results, name='backtest_results'),

    # 백테스트 상세 (신호 포함)
    path('api/backtest/detail/<int:backtest_id>/', api_views.get_backtest_detail, name='backtest_detail'),
]

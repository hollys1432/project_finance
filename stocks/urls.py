# stocks/urls.py

from django.urls import path
from django.views.generic import RedirectView
from . import views, api_views, market_views

app_name = 'stocks'

urlpatterns = [
    # 메인 페이지로 리다이렉트 (홈 화면에 검색 기능이 있음)
    path('', RedirectView.as_view(url='/', permanent=False), name='index'),

    # 한국 주식 상세 페이지
    path('company/<int:company_id>/', views.CompanyDetailView.as_view(), name='company_detail'),

    # 미국 주식 상세 페이지
    path('us-company/<int:company_id>/', views.USCompanyDetailView.as_view(), name='us_company_detail'),

    # 시장 지수 API 엔드포인트
    path('api/market/indices/', market_views.market_all_indices, name='api_market_indices'),
    path('api/market/indices/<str:index_id>/', market_views.market_index_detail, name='api_market_index_detail'),
    path('api/market/realtime/', market_views.market_realtime_quotes, name='api_market_realtime'),

    # API 엔드포인트
    path('api/search/', api_views.search_companies, name='api_search'),
    path('api/company/<int:company_id>/data/', api_views.get_company_data, name='api_company_data'),
    path('api/company/<int:company_id>/price-range/', api_views.get_price_range, name='api_price_range'),
    path('api/us-company/<int:company_id>/data/', api_views.get_us_company_data, name='api_us_company_data'),
    path('api/us-company/<int:company_id>/price-range/', api_views.get_us_price_range, name='api_us_price_range'),

    # 호환성을 위한 기존 URL 유지
    path('search/', api_views.search_companies, name='search_companies'),
]
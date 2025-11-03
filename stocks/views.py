# stocks/views.py

from django.views.generic import TemplateView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Max, Min, Avg
from datetime import datetime, timedelta
from .models import CompanyInfo, PriceData, USCompanyInfo, USPriceData

class HomeView(TemplateView):
    """메인 홈 페이지 - 환영 화면"""
    template_name = 'stocks/home.html'

class IndexView(TemplateView):
    """메인 페이지 - 통합 주식 검색 인터페이스"""
    template_name = 'stocks/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 최근 30일 데이터가 있는 종목들
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # 한국 주식 인기 종목
        popular_kr_companies = CompanyInfo.objects.filter(
            is_active=True,
            prices__date__gte=start_date
        ).distinct()[:5]
        
        # 미국 주식 인기 종목
        popular_us_companies = USCompanyInfo.objects.filter(
            is_active=True,
            prices__date__gte=start_date
        ).distinct()[:5]
        
        context['popular_kr_companies'] = popular_kr_companies
        context['popular_us_companies'] = popular_us_companies
        context['total_kr_companies'] = CompanyInfo.objects.filter(is_active=True).count()
        context['total_us_companies'] = USCompanyInfo.objects.filter(is_active=True).count()
        
        return context


class CompanyDetailView(DetailView):
    """한국 회사 상세 페이지 - 차트 및 분석"""
    model = CompanyInfo
    template_name = 'stocks/company_detail.html'
    context_object_name = 'company'
    pk_url_kwarg = 'company_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.object
        
        # 기본 통계 정보 계산 (180일) - 모델의 메서드 사용
        stats = company.calculate_statistics(days=180)
        context['stats'] = stats
        
        # 최신 가격 정보 - 모델의 메서드 사용
        latest_price = company.get_latest_price()
        context['latest_price'] = latest_price
        
        # 52주 최고/최저
        one_year_ago = datetime.now().date() - timedelta(days=365)
        year_prices = PriceData.objects.filter(
            stock=company,
            date__gte=one_year_ago
        ).aggregate(
            max_price=Max('close_price'),
            min_price=Min('close_price'),
            avg_volume=Avg('volume')
        )
        context['year_stats'] = year_prices
        
        # 시장 정보
        context['market'] = company.market or 'N/A'
        
        return context


class USCompanyDetailView(DetailView):
    """미국 회사 상세 페이지 - 차트 및 분석"""
    model = USCompanyInfo
    template_name = 'stocks/us_company_detail.html'
    context_object_name = 'company'
    pk_url_kwarg = 'company_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.object
        
        # 기본 통계 정보 계산 (180일) - 모델의 메서드 사용
        stats = company.calculate_statistics(days=180)
        context['stats'] = stats
        
        # 최신 가격 정보 - 모델의 메서드 사용
        latest_price = company.get_latest_price()
        context['latest_price'] = latest_price
        
        # 52주 최고/최저
        one_year_ago = datetime.now().date() - timedelta(days=365)
        year_prices = USPriceData.objects.filter(
            stock=company,
            date__gte=one_year_ago
        ).aggregate(
            max_price=Max('close_price'),
            min_price=Min('close_price'),
            avg_volume=Avg('volume'),
            max_adj_close=Max('adj_close_price'),
            min_adj_close=Min('adj_close_price')
        )
        context['year_stats'] = year_prices
        
        # 시장 정보
        context['exchange'] = company.exchange or 'N/A'
        context['sector'] = company.sector or 'N/A'
        context['industry'] = company.industry or 'N/A'
        context['currency'] = company.currency or 'USD'
        
        return context
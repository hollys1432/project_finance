"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from stocks.market_views import MarketDashboardView
from django.views.generic import TemplateView

urlpatterns = [
    path('', MarketDashboardView.as_view(), name='home'),  # 루트 URL - 시장 대시보드
    path('admin/', admin.site.urls),
    path('stocks/', include('stocks.urls')),  # stocks 접두사 추가
    path('quant/', include('quant.urls')),  # quant 접두사 추가
]

# 개발 환경에서만 정적 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
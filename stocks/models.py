# stocks/models.py

from django.db import models
from django.urls import reverse
from datetime import datetime, timedelta

class CompanyInfo(models.Model):
    company_code = models.CharField(max_length=20, unique=True, db_index=True)
    company_name = models.CharField(max_length=200, db_index=True)
    market = models.CharField(max_length=50, null=True, blank=True)
    listing_date = models.DateField(null=True, blank=True, help_text="상장일")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'company_info'
        verbose_name = '회사 정보'
        verbose_name_plural = '회사 정보'
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['company_code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.company_name} ({self.company_code})"
    
    def get_absolute_url(self):
        """상세 페이지 URL 반환"""
        return reverse('stocks:company_detail', kwargs={'company_id': self.id})
    
    def get_latest_price(self):
        """최신 주가 정보 반환"""
        latest_price = self.prices.order_by('-date').first()
        return latest_price
    
    def get_price_range(self, days=30):
        """지정된 기간의 주가 데이터 반환"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        return self.prices.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
    
    def calculate_statistics(self, days=180):
        """통계 정보 계산"""
        price_data = self.get_price_range(days)
        
        if not price_data.exists():
            return None
        
        prices = [float(p.close_price) for p in price_data if p.close_price]
        volumes = [int(p.volume) for p in price_data if p.volume]
        
        if not prices:
            return None
        
        stats = {
            'current_price': prices[-1] if prices else 0,
            'max_price': max(prices),
            'min_price': min(prices),
            'avg_price': sum(prices) / len(prices),
            'price_change': prices[-1] - prices[-2] if len(prices) >= 2 else 0,
            'avg_volume': sum(volumes) / len(volumes) if volumes else 0,
            'data_count': len(prices)
        }
        
        # 변화율 계산
        if len(prices) >= 2 and prices[-2] != 0:
            stats['price_change_rate'] = (stats['price_change'] / prices[-2]) * 100
        else:
            stats['price_change_rate'] = 0
        
        return stats


class PriceData(models.Model):
    stock = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, related_name="prices")
    stock_name = models.CharField(max_length=200)
    date = models.DateField(db_index=True)
    open_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    high_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    low_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    close_price = models.DecimalField(max_digits=15, decimal_places=2)
    volume = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'price_data'
        verbose_name = '주가 데이터'
        verbose_name_plural = '주가 데이터'
        unique_together = ['stock', 'date']
        indexes = [
            models.Index(fields=['stock', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['stock', '-date']),
        ]
    
    def __str__(self):
        return f"{self.stock_name} - {self.date}: {self.close_price}원"
    
    @property
    def price_change(self):
        """전일 대비 가격 변동"""
        try:
            previous_day = PriceData.objects.filter(
                stock=self.stock,
                date__lt=self.date
            ).order_by('-date').first()
            
            if previous_day and previous_day.close_price:
                return float(self.close_price) - float(previous_day.close_price)
            return 0
        except:
            return 0
    
    @property
    def price_change_rate(self):
        """전일 대비 변화율 (%)"""
        try:
            previous_day = PriceData.objects.filter(
                stock=self.stock,
                date__lt=self.date
            ).order_by('-date').first()
            
            if previous_day and previous_day.close_price and float(previous_day.close_price) != 0:
                change = float(self.close_price) - float(previous_day.close_price)
                return (change / float(previous_day.close_price)) * 100
            return 0
        except:
            return 0


class USCompanyInfo(models.Model):
    """미국 상장사 기본정보"""
    symbol = models.CharField(max_length=10, unique=True, db_index=True, help_text="티커 심볼 (예: AAPL)")
    company_name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    market_cap = models.BigIntegerField(blank=True, null=True)
    exchange = models.CharField(max_length=20, blank=True, null=True, help_text="NASDAQ, NYSE 등")
    country = models.CharField(max_length=10, default='US')
    currency = models.CharField(max_length=5, default='USD')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "US Company Info"
        verbose_name_plural = "US Company Infos"
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['company_name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.symbol} {self.company_name}"
    
    def get_absolute_url(self):
        """상세 페이지 URL 반환"""
        return reverse('stocks:us_company_detail', kwargs={'company_id': self.id})
    
    def get_latest_price(self):
        """최신 주가 정보 반환"""
        latest_price = self.prices.order_by('-date').first()
        return latest_price
    
    def get_price_range(self, days=30):
        """지정된 기간의 주가 데이터 반환"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        return self.prices.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
    
    def calculate_statistics(self, days=180):
        """통계 정보 계산"""
        price_data = self.get_price_range(days)
        
        if not price_data.exists():
            return None
        
        prices = [float(p.close_price) for p in price_data if p.close_price]
        adj_close_prices = [float(p.adj_close_price) if p.adj_close_price else float(p.close_price) for p in price_data if p.close_price or p.adj_close_price]
        volumes = [int(p.volume) for p in price_data if p.volume]
        
        if not prices:
            return None
        
        stats = {
            'current_price': prices[-1] if prices else 0,
            'max_price': max(prices),
            'min_price': min(prices),
            'avg_price': sum(prices) / len(prices),
            'price_change': prices[-1] - prices[-2] if len(prices) >= 2 else 0,
            'avg_volume': sum(volumes) / len(volumes) if volumes else 0,
            'adj_close_price': adj_close_prices[-1] if adj_close_prices else 0,
            'adj_price_change': adj_close_prices[-1] - adj_close_prices[-2] if len(adj_close_prices) >= 2 else 0,
            'data_count': len(prices)
        }
        
        # 변화율 계산
        if len(prices) >= 2 and prices[-2] != 0:
            stats['price_change_rate'] = (stats['price_change'] / prices[-2]) * 100
        else:
            stats['price_change_rate'] = 0
        
        # 조정종가 변화율 계산
        if len(adj_close_prices) >= 2 and adj_close_prices[-2] != 0:
            stats['adj_price_change_rate'] = (stats['adj_price_change'] / adj_close_prices[-2]) * 100
        else:
            stats['adj_price_change_rate'] = 0
        
        return stats


class USPriceData(models.Model):
    """미국 주식 일별 가격 데이터"""
    stock = models.ForeignKey(USCompanyInfo, on_delete=models.CASCADE, related_name="prices")
    symbol = models.CharField(max_length=10, db_index=True)  # 중복이지만 쿼리 성능용
    date = models.DateField()
    open_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    high_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    low_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    close_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    adj_close_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True, 
                                        help_text="배당/분할 조정 종가")
    volume = models.BigIntegerField(blank=True, null=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["stock", "date"], name="uniq_us_stock_date"),
        ]
        indexes = [
            models.Index(fields=["stock", "date"]),
            models.Index(fields=["symbol", "date"]),
            models.Index(fields=["date"]),
            models.Index(fields=["stock", "-date"]),
        ]
        verbose_name = "US Price Data"
        verbose_name_plural = "US Price Data"

    def __str__(self):
        return f"{self.symbol} {self.date}"
    
    @property
    def price_change(self):
        """전일 대비 가격 변동"""
        try:
            previous_day = USPriceData.objects.filter(
                stock=self.stock,
                date__lt=self.date
            ).order_by('-date').first()
            
            if previous_day and previous_day.close_price and self.close_price:
                return float(self.close_price) - float(previous_day.close_price)
            return 0
        except:
            return 0
    
    @property
    def price_change_rate(self):
        """전일 대비 변화율 (%)"""
        try:
            previous_day = USPriceData.objects.filter(
                stock=self.stock,
                date__lt=self.date
            ).order_by('-date').first()
            
            if previous_day and previous_day.close_price and self.close_price and float(previous_day.close_price) != 0:
                change = float(self.close_price) - float(previous_day.close_price)
                return (change / float(previous_day.close_price)) * 100
            return 0
        except:
            return 0


# 추가적인 유틸리티 모델들
class MarketIndex(models.Model):
    """시장 지수 정보"""
    market_name = models.CharField(max_length=50, unique=True)
    index_name = models.CharField(max_length=100)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    change_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    change_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'market_index'
        verbose_name = '시장 지수'
        verbose_name_plural = '시장 지수'
    
    def __str__(self):
        return f"{self.market_name} - {self.index_name}: {self.current_value}"


class WatchList(models.Model):
    """관심 종목 (사용자 기능 확장시 사용)"""
    user_session = models.CharField(max_length=100)  # 세션 기반으로 임시 구현
    company = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'watch_list'
        verbose_name = '관심 종목'
        verbose_name_plural = '관심 종목'
        unique_together = ['user_session', 'company']
    
    def __str__(self):
        return f"{self.user_session} - {self.company.company_name}"

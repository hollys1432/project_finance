from django.db import models
from stocks.models import CompanyInfo, USCompanyInfo
from django.utils import timezone


class Strategy(models.Model):
    """퀀트 전략"""
    STRATEGY_TYPES = [
        ('ma_cross', '이동평균 크로스오버'),
        ('rsi', 'RSI 전략'),
        ('bollinger', '볼린저밴드'),
        ('momentum', '모멘텀'),
        ('mean_reversion', '평균회귀'),
        ('custom', '커스텀'),
    ]

    name = models.CharField(max_length=200, verbose_name='전략명')
    strategy_type = models.CharField(max_length=50, choices=STRATEGY_TYPES, verbose_name='전략 유형')
    description = models.TextField(blank=True, verbose_name='설명')
    parameters = models.JSONField(default=dict, verbose_name='파라미터')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '전략'
        verbose_name_plural = '전략'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_strategy_type_display()})"


class Backtest(models.Model):
    """백테스트 결과"""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, verbose_name='전략')

    # 종목 정보 (한국 또는 미국)
    kr_stock = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, null=True, blank=True, verbose_name='한국 종목')
    us_stock = models.ForeignKey(USCompanyInfo, on_delete=models.CASCADE, null=True, blank=True, verbose_name='미국 종목')

    # 백테스트 기간
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(verbose_name='종료일')

    # 백테스트 결과
    total_return = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='총 수익률(%)')
    annual_return = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='연 수익률(%)')
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, verbose_name='샤프 비율')
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='최대 낙폭(%)')
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='승률(%)')
    total_trades = models.IntegerField(default=0, verbose_name='총 거래 횟수')

    # 초기 자본금
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2, default=10000000, verbose_name='초기 자본금')
    final_capital = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='최종 자본금')

    # 기타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')

    class Meta:
        verbose_name = '백테스트'
        verbose_name_plural = '백테스트'
        ordering = ['-created_at']

    def __str__(self):
        stock_name = self.kr_stock.company_name if self.kr_stock else self.us_stock.company_name
        return f"{self.strategy.name} - {stock_name} ({self.start_date}~{self.end_date})"


class Signal(models.Model):
    """거래 신호"""
    SIGNAL_TYPES = [
        ('buy', '매수'),
        ('sell', '매도'),
    ]

    backtest = models.ForeignKey(Backtest, on_delete=models.CASCADE, related_name='signals', verbose_name='백테스트')

    date = models.DateField(verbose_name='신호 발생일')
    signal_type = models.CharField(max_length=10, choices=SIGNAL_TYPES, verbose_name='신호 유형')
    price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='가격')
    quantity = models.IntegerField(default=0, verbose_name='수량')
    reason = models.TextField(blank=True, verbose_name='신호 발생 이유')

    # 신호 관련 지표값들 (JSON으로 저장)
    indicator_values = models.JSONField(default=dict, verbose_name='지표값')

    class Meta:
        verbose_name = '거래 신호'
        verbose_name_plural = '거래 신호'
        ordering = ['date']

    def __str__(self):
        return f"{self.get_signal_type_display()} - {self.date} ({self.price})"

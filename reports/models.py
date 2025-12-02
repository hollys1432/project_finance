from django.db import models
from django.utils import timezone


class MarketReport(models.Model):
    """시장 분석 보고서"""
    REPORT_TYPE_CHOICES = [
        ('daily', '일간'),
        ('weekly', '주간'),
        ('monthly', '월간'),
    ]

    MARKET_CHOICES = [
        ('kr', '한국'),
        ('us', '미국'),
        ('all', '전체'),
    ]

    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES, default='daily')
    market = models.CharField(max_length=5, choices=MARKET_CHOICES, default='all')
    report_date = models.DateField(default=timezone.now)

    # 시장 지수 정보
    market_indices = models.JSONField(default=dict, blank=True)

    # 섹터별 분석
    sector_analysis = models.JSONField(default=dict, blank=True)

    # 거래량 상위 종목
    top_volume_stocks = models.JSONField(default=list, blank=True)

    # 가격 변동률 상위/하위 종목
    top_gainers = models.JSONField(default=list, blank=True)
    top_losers = models.JSONField(default=list, blank=True)

    # 기술적 분석 요약
    technical_summary = models.JSONField(default=dict, blank=True)

    # 보고서 생성 시간
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-report_date', '-created_at']
        unique_together = ['report_type', 'market', 'report_date']
        indexes = [
            models.Index(fields=['-report_date']),
            models.Index(fields=['report_type', 'market']),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} {self.get_market_display()} 보고서 - {self.report_date}"


class ScheduledReport(models.Model):
    """정기 보고서 설정"""
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=10, choices=MarketReport.REPORT_TYPE_CHOICES)
    market = models.CharField(max_length=5, choices=MarketReport.MARKET_CHOICES, default='all')

    is_active = models.BooleanField(default=True)

    # 생성 스케줄
    schedule_time = models.TimeField(help_text="보고서 생성 시간")

    # 이메일 전송 설정 (추후 구현)
    send_email = models.BooleanField(default=False)
    email_recipients = models.JSONField(default=list, blank=True)

    # 마지막 생성 시간
    last_generated = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['report_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

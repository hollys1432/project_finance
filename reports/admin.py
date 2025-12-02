from django.contrib import admin
from .models import MarketReport, ScheduledReport


@admin.register(MarketReport)
class MarketReportAdmin(admin.ModelAdmin):
    list_display = ['report_date', 'report_type', 'market', 'created_at']
    list_filter = ['report_type', 'market', 'report_date']
    search_fields = ['report_date']
    ordering = ['-report_date', '-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('report_type', 'market', 'report_date')
        }),
        ('데이터', {
            'fields': ('market_indices', 'sector_analysis', 'top_volume_stocks',
                      'top_gainers', 'top_losers', 'technical_summary'),
            'classes': ('collapse',)
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'market', 'schedule_time', 'is_active', 'last_generated']
    list_filter = ['report_type', 'market', 'is_active']
    search_fields = ['name']
    ordering = ['report_type', 'name']

    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'report_type', 'market', 'is_active')
        }),
        ('스케줄 설정', {
            'fields': ('schedule_time', 'last_generated')
        }),
        ('이메일 설정', {
            'fields': ('send_email', 'email_recipients'),
            'classes': ('collapse',)
        }),
    )

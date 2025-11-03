from django.contrib import admin
from .models import CompanyInfo, PriceData, MarketIndex, WatchList

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'company_code', 'market', 'is_active']
    list_filter = ['market', 'is_active']
    search_fields = ['company_name', 'company_code']
    list_per_page = 50
    ordering = ['company_name']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('company_name', 'company_code', 'market')
        }),
        ('상장 정보', {
            'fields': ('is_active',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 수정시
            return self.readonly_fields + ['company_code']
        return self.readonly_fields

@admin.register(PriceData)
class PriceDataAdmin(admin.ModelAdmin):
    list_display = ['stock_name', 'date', 'close_price', 'volume', 'price_change_display']
    list_filter = ['date', 'stock__market']
    search_fields = ['stock__company_name', 'stock__company_code']
    date_hierarchy = 'date'
    list_per_page = 100
    ordering = ['-date', 'stock__company_name']
    
    def price_change_display(self, obj):
        change = obj.price_change
        if change > 0:
            return f"+{change:,.0f}원"
        elif change < 0:
            return f"{change:,.0f}원"
        else:
            return "0원"
    price_change_display.short_description = '전일대비'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('stock', 'date')
        }),
        ('가격 정보', {
            'fields': ('open_price', 'high_price', 'low_price', 'close_price')
        }),
        ('거래 정보', {
            'fields': ('volume',)
        }),
    )

@admin.register(MarketIndex)
class MarketIndexAdmin(admin.ModelAdmin):
    list_display = ['market_name', 'index_name', 'current_value', 'change_value', 'change_rate', 'updated_at']
    list_filter = ['market_name', 'updated_at']
    ordering = ['market_name']

@admin.register(WatchList)
class WatchListAdmin(admin.ModelAdmin):
    list_display = ['user_session', 'company', 'created_at']
    list_filter = ['created_at']
    search_fields = ['company__company_name', 'user_session']

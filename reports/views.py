from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView
from django.utils import timezone
from datetime import datetime, timedelta
from .models import MarketReport, ScheduledReport
from .utils.report_generator import MarketAnalyzer


class ReportListView(ListView):
    """보고서 목록"""
    model = MarketReport
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        queryset = MarketReport.objects.all()

        # 필터링
        report_type = self.request.GET.get('type')
        market = self.request.GET.get('market')

        if report_type:
            queryset = queryset.filter(report_type=report_type)
        if market:
            queryset = queryset.filter(market=market)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_types'] = MarketReport.REPORT_TYPE_CHOICES
        context['markets'] = MarketReport.MARKET_CHOICES
        return context


class ReportDetailView(DetailView):
    """보고서 상세"""
    model = MarketReport
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'


def generate_report(request):
    """보고서 생성"""
    report_type = request.GET.get('type', 'daily')
    market = request.GET.get('market', 'all')
    report_date_str = request.GET.get('date')

    if report_date_str:
        try:
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = timezone.now().date()
    else:
        report_date = timezone.now().date()

    # 기존 보고서 확인
    existing_report = MarketReport.objects.filter(
        report_type=report_type,
        market=market,
        report_date=report_date
    ).first()

    if existing_report:
        return JsonResponse({
            'status': 'exists',
            'message': '이미 생성된 보고서가 있습니다.',
            'report_id': existing_report.id
        })

    # 분석기 생성
    analyzer = MarketAnalyzer(market=market, report_date=report_date)

    # 데이터 생성
    market_indices = analyzer.generate_market_indices()
    top_volume = analyzer.get_top_volume_stocks(limit=20)
    gainers, losers = analyzer.get_top_gainers_losers(limit=20)
    sector_analysis = analyzer.get_sector_analysis()
    technical_summary = analyzer.get_technical_summary()

    # 보고서 저장
    report = MarketReport.objects.create(
        report_type=report_type,
        market=market,
        report_date=report_date,
        market_indices=market_indices,
        top_volume_stocks=top_volume,
        top_gainers=gainers,
        top_losers=losers,
        sector_analysis=sector_analysis,
        technical_summary=technical_summary,
    )

    return JsonResponse({
        'status': 'success',
        'message': '보고서가 생성되었습니다.',
        'report_id': report.id
    })


def export_pdf(request, pk):
    """인쇄용 페이지 (브라우저 인쇄 기능 활용)"""
    report = get_object_or_404(MarketReport, pk=pk)

    # 인쇄용 템플릿 렌더링
    return render(request, 'reports/report_pdf.html', {
        'report': report,
        'print_mode': True
    })

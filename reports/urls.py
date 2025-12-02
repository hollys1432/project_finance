from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportListView.as_view(), name='list'),
    path('<int:pk>/', views.ReportDetailView.as_view(), name='detail'),
    path('generate/', views.generate_report, name='generate'),
    path('<int:pk>/export/pdf/', views.export_pdf, name='export_pdf'),
]

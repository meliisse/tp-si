
from django.urls import path
from .api_views import DashboardStatsView, ChartDataView, incident_reports, reclamation_reports, advanced_kpis

urlpatterns = [
	path('api/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
	path('api/charts/', ChartDataView.as_view(), name='dashboard-charts'),
	path('api/reports/incidents/', incident_reports, name='incident-reports'),
	path('api/reports/reclamations/', reclamation_reports, name='reclamation-reports'),
	path('api/kpis/advanced/', advanced_kpis, name='advanced-kpis'),
]

from django.urls import path
from .api_views import DashboardStatsView

urlpatterns = [
	path('api/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
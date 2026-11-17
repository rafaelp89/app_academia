from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('charts/frequency.svg', views.frequency_chart_svg, name='chart_frequency'),
    path('charts/weekly-rate.svg', views.weekly_rate_chart_svg, name='chart_weekly_rate'),
]


from django.urls import path
from . import views

app_name = 'exports'

urlpatterns = [
    path('', views.exports_hub, name='hub'),
    path('csv/', views.export_csv, name='export_csv'),
    path('json/', views.export_json, name='export_json'),
    path('restore/', views.restore_json, name='restore_json'),
]


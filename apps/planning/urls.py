from django.urls import path
from . import views

app_name = 'planning'

urlpatterns = [
    path('', views.plan_detail, name='plan_detail'),
    path('phases/<int:pk>/', views.phase_detail, name='phase_detail'),
    path('adjustments/', views.adjustment_history, name='adjustment_history'),
    path('reorganize-backlog/', views.reorganize_backlog, name='reorganize_backlog'),
    path('advance-phase/', views.advance_phase, name='advance_phase'),
]


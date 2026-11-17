from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    path('today/', views.today_workout, name='today_workout'),
    path('workout/<int:pk>/', views.workout_session, name='workout_session'),
    path('toggle/<int:record_id>/', views.toggle_exercise_checkbox, name='toggle_exercise_checkbox'),
    path('weekly/', views.weekly_view, name='weekly_view'),
    path('calendar/', views.calendar_view, name='calendar_view'),
]


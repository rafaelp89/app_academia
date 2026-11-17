from django.urls import path
from . import views

app_name = 'training'

urlpatterns = [
    path('exercises/', views.exercise_list, name='exercise_list'),
    path('exercises/<int:pk>/', views.exercise_detail, name='exercise_detail'),
    path('templates/', views.template_list, name='template_list'),
]


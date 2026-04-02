"""
URLs web para o app screenshots
"""
from django.urls import path
from . import views

urlpatterns = [
    path('screenshots/', views.screenshot_list, name='screenshot_list'),
]
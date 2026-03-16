from django.urls import path
from . import views_web

urlpatterns = [
    path('screenshots/', views_web.screenshot_list, name='screenshot_list'),
]
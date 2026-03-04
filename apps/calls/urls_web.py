from django.urls import path
from . import views_web

urlpatterns = [
    path('calls/', views_web.call_list, name='calls'),
    path('calls/statistics/', views_web.call_statistics, name='call_statistics'),
]
from django.urls import path
from apps.accounts import views_web

urlpatterns = [
    path('dashboard/', views_web.dashboard, name='dashboard'),
    path('profile/', views_web.profile, name='profile'),
    path('settings/', views_web.settings, name='settings'),
    path('login/', views_web.login_view, name='login'),
    path('register/', views_web.register_view, name='register'),
    path('logout/', views_web.logout_view, name='logout'),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Criando o router
router = DefaultRouter()

# Registrando os ViewSets com basename explícito
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profiles', views.ProfileViewSet, basename='profile')

# URLs da API
urlpatterns = [
    # Inclui as URLs do router
    path('', include(router.urls)),

    # URLs adicionais
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.CurrentUserView.as_view(), name='current_user'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('statistics/', views.user_statistics, name='user_statistics'),
]
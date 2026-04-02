"""
URLs da API para o app screenshots
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'screenshots', views.ScreenshotViewSet, basename='screenshot')

print("✅ URLs do screenshots carregadas!")
print("   - /upload/ disponível")
print("   - /debug/devices/ disponível")
print("   - /debug/screenshots/ disponível")

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', views.upload_screenshot, name='upload_screenshot'),
    path('debug/devices/', views.debug_list_devices, name='debug_devices'),
    path('debug/screenshots/', views.debug_list_screenshots, name='debug_screenshots'),
]
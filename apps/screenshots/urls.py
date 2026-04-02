from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # ← importação relativa funciona

router = DefaultRouter()
router.register(r'screenshots', views.ScreenshotViewSet, basename='screenshot')

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', views.upload_screenshot, name='upload_screenshot'),
]
# apps/screenshots/urls.py
print("✅ URLs do screenshots carregadas!")
print("   - /upload/ disponível")
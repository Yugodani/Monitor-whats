from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'screenshots', views.ScreenshotViewSet, basename='screenshot')

urlpatterns = [
    path('', include(router.urls)),
    # Endpoint adicional para upload simplificado
    path('screenshots/upload/', views.upload_screenshot, name='upload_screenshot'),
]
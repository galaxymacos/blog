from django.urls import path, include
from rest_framework import routers

from .views import PhotoViewSet

app_name = "api"

router = routers.DefaultRouter()
router.register(r'photo', PhotoViewSet, basename="photo")

urlpatterns = [
    path('', include(router.urls))
]
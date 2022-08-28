from django.urls import path
from .views import *
app_name = 'deepl'

urlpatterns = [
    path("", index, name="index"),
]
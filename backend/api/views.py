from django.shortcuts import render
from rest_framework import viewsets

from .models import Photo
from .serializers import PhotoSerializer


# Create your views here.
class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer

from django.db import models


# Create your models here.
class Photo(models.Model):
    title = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

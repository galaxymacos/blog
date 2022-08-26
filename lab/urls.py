from django.urls import path

from lab.views import twilio_webhook, cloudbeds_webhook

app_name = 'lab'
urlpatterns = [
    path('twilio-webhook/', twilio_webhook, name='twilio_webhook'),
    path('cloudbeds-webhook/', cloudbeds_webhook, name='cloudbeds_webhook'),
]
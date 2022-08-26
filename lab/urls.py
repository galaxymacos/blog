from django.urls import path

from lab.views import twilio_webhook, cloudbeds_webhook, cloudbeds_login_redirect, cloudbeds_login, try_refresh, \
    subscribe_to_webhook, list_webhooks, delete_webhooks

app_name = 'lab'
urlpatterns = [
    path('twilio-webhook/', twilio_webhook, name='twilio_webhook'),
    path('cloudbeds-webhook/', cloudbeds_webhook, name='cloudbeds_webhook'),
    path('oauth2/callback/', cloudbeds_login_redirect, name='oauth_login_redirect'),
    path('login/', cloudbeds_login, name='oauth_login'),
    path('refresh/', try_refresh, name='oauth_refresh'),
    path("subscribe-to-webhook/", subscribe_to_webhook, name="subscribe_to_webhook"),
    path("list-webhooks/", list_webhooks, name="list_webhooks"),
    path("delete-webhooks/", delete_webhooks, name="delete_webhooks"),
]
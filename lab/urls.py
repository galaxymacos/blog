from django.urls import path

from lab.views import *
app_name = 'lab'
urlpatterns = [
    # Webhooks
    path('twilio-webhook/', on_sms_receive, name='twilio_webhook'),
    path('on-reservation-created/', on_reservation_created, name='on_reservation_created'),
    path('on-reservation-status-changed/', on_reservation_status_changed, name='on_reservation_status_changed'),
    path('on-reservation-dates-changed/', on_reservation_dates_changed, name='on_reservation_dates_changed'),
    path('on-reservation-accommodation-type-changed', on_reservation_accommodation_type_changed, name='on_reservation_accommodation_type_changed'),
    path('on-reservation-accommodation-changed/', on_reservation_accommodation_changed, name='on_reservation_accommodation_changed'),


    path('oauth2/callback/', cloudbeds_login_redirect, name='oauth_login_redirect'),
    path('login/', cloudbeds_login, name='oauth_login'),
    path('refresh/', try_refresh, name='oauth_refresh'),
    path("subscribe-to-webhook/", subscribe_to_webhook, name="subscribe_to_webhook"),
    path("list-webhooks/", list_webhooks, name="list_webhooks"),
    path("delete-webhooks/", delete_webhooks, name="delete_webhooks"),
]
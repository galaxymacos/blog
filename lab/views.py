import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

import json
from datetime import datetime, timedelta

import requests
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from twilio.rest import Client

from blog.settings import *
from deepl.util import translate


# Create your views here.
def send_message(phone_number, message):
    account_sid = TWILIO_ACCOUNT_SID
    auth_token = TWILIO_AUTH_TOKEN
    twilio_phone_number = TWILIO_PHONE_NUMBER
    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=phone_number
        )
        print(f"Message {message.sid} sent to {phone_number}")
        return
    except Exception as e:
        print(e)
        print("Error sending message to {}".format(phone_number))


@require_POST
@csrf_exempt
def twilio_webhook(request):    # Get the post QueryDict from the request.
    if request.method == 'POST':
        try:
            data = request.POST
            phone = data['From']
            body = data['Body']
            logging.debug(f"{datetime.now()}: Received message from {phone} with body {body}")
            # Send translation to YuRuan
            message_chinese = translate(body, "ZH")
            send_message(MANAGER_PHONE_NUMBER, message_chinese)
            # message_english = translate(body, "en")
            # send_message(RECEPTIONIST_PHONE_NUMBER, message_english)
            return HttpResponse("Twilio webhook: POST received")
        except Exception as e:
            logging.error(f"Error receiving twilio webhook: {e}")
            return JsonResponse({"Success": False, "Error": str(e)})
    else:
        logging.info("Twilio webhook: GET received")
        return HttpResponse("Twilio webhook: GET received")


@require_POST
@csrf_exempt
def cloudbeds_webhook(request):
    if request.method == "POST":
        try:
            logging.info("Cloudbeds webhook: POST received")
            # Get the JSON data from the request body
            data = json.loads(request.body)
            reservation_id = data['reservation_id']
            response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getGuest",
                                    headers={"Authorization": f"Bearer {CONFIG_DATA['access_token']}",},
                                    params={"reservationID": reservation_id})
            cell_phone = trim_phone(response.json()["data"]["cellPhone"])
            phone = trim_phone(response.json()["data"]["phone"])
            cell_phone = cell_phone if cell_phone else phone
            guest_firstname = response.json()["data"]["firstName"]
            guest_lastname = response.json()["data"]["lastName"]
            if data['startDate'] == datetime.now().strftime("%Y-%m-%d") and datetime.now().hour >= 8:
                message = f"Bonjour {guest_firstname}, vous avez une réservation à l'Hôtel Cowansville pour aujourd'hui. Veuillez vous enregistrer après 15h30. Nous avons un personnel limité pour nettoyer les chambres, donc tout enregistrement anticipé avant 15h00 sera refusé.Votre clé sera prête pour vous à la réception pour un enregistrement plus rapide si nous avons bien reçu votre paiement."
            else:
                message = f"Bonjour, {guest_firstname}, votre réservation a été confirmée au {data['startDate']}. Si vous avez des questions, veuillez nous envoyer un courriel à info@cowansvillehotel.com."
            send_message(cell_phone, message)
            logging.debug(f"{datetime.now()}Sent reservation confirmation message to {guest_firstname} {guest_lastname} at {cell_phone}")

        except Exception as e:
            logging.error(f"{datetime.now()} - Error in cloudbeds webhook: " + str(e))
        return HttpResponse("Cloudbeds webhook: POST received")
    else:
        logging.error(f"{datetime.now()} - Cloudbeds webhook: GET received")


if DEBUG:
    REDIRECT_URI = "https://127.0.0.1:8000/lab/oauth2/callback"
else:
    REDIRECT_URI = "https://xunruan.ca/lab/oauth2/callback"

oauth_url = "https://hotels.cloudbeds.com/api/v1.1/oauth?" \
            f"client_id={CLOUDBEDS_CLIENT_ID}" \
            "&" \
            f"redirect_uri={REDIRECT_URI}" \
            "&" \
            "response_type=code"


def cloudbeds_login(request):
    # send user to cloudbeds login page (oauth), cloudbeds is responsible for redirecting user to callback page
    return redirect(oauth_url)


def cloudbeds_login_redirect(request):
    with open(BASE_DIR / "config_data.json", "r") as f:
        local_config_data = json.load(f)
    code = request.GET.get('code')
    codes = exchange_code(request, code)
    local_config_data['access_token'] = codes[0]
    local_config_data['refresh_token'] = codes[1]
    local_config_data['expires_in'] = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    with open(BASE_DIR / "config_data.json", "w") as f:
        json.dump(local_config_data, f)
    return HttpResponse("Successful")


def try_refresh(request):
    # Refresh access token (should be called before access token is expired, which is 1 hour)
    if datetime.strptime(str(CONFIG_DATA['expires_in']), "%Y-%m-%d %H:%M:%S") < datetime.now():
        return cloudbeds_login(request)
    else:
        if refresh():
            return HttpResponse('Access token refreshed')
        else:
            return HttpResponse('Access token refresh failed')


def refresh():
    try:
        with open(BASE_DIR / "config_data.json", "r") as f:
            local_config_data = json.load(f)
        data = {
            "grant_type": "refresh_token",
            "client_id": CLOUDBEDS_CLIENT_ID,
            "client_secret": CLOUDBEDS_CLIENT_SECRET,
            "refresh_token": local_config_data['refresh_token'],
        }
        header = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post("https://hotels.cloudbeds.com/api/v1.1/access_token", data=data, headers=header)
        credentials = response.json()
        local_config_data['access_token'] = credentials['access_token']
        local_config_data['refresh_token'] = credentials['refresh_token']
        local_config_data['expires_in'] = (datetime.now() + timedelta(minutes=59)).strftime("%Y-%m-%d %H:%M:%S")
        with open(BASE_DIR / "config_data.json", "w") as f:
            json.dump(local_config_data, f)
        # send_message(MANAGER_PHONE_NUMBER, "Access token refreshed")
        logging.info("Access token refreshed at {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    except Exception as e:
        logging.warning(f"Error refreshing access token at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        send_message(MANAGER_PHONE_NUMBER, "Access token refresh failed, error:" + str(e))


def exchange_code(request, code):
    # Exchange authorization code for access token and refresh token
    data = {
        "client_id": CLOUDBEDS_CLIENT_ID,
        "client_secret": CLOUDBEDS_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        f"redirect_uri": {REDIRECT_URI},
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post("https://hotels.cloudbeds.com/api/v1.1/access_token", data=data, headers=headers)
    credentials = response.json()
    access_token = credentials['access_token']
    refresh_token = credentials['refresh_token']

    return access_token, refresh_token


def trim_phone(phone):
    valid_phone = f"+1{(phone.replace('-', '').replace(' ', ''))[-10:]}"
    if len(valid_phone) != 12:
        return None
    return valid_phone


# Webhook
def subscribe_to_webhook(request):
    with open(BASE_DIR / "config_data.json", "r") as f:
        local_config_data = json.load(f)
    try:
        headers_myblog = {
            "Authorization": f"Bearer {local_config_data['access_token']}",
        }

        data_myblog = {
            "endpointUrl": "https://xunruan.ca/lab/cloudbeds-webhook/",
            "object": "reservation",
            "action": "created"
        }
        response_myblog = requests.post("https://hotels.cloudbeds.com/api/v1.1/postWebhook", headers=headers_myblog,
                                        data=data_myblog)

        logging.debug(f"{datetime.now()} Subscribed to myblog: {response_myblog.status_code}")
    except Exception as e:
        print(e)
        logging.error(f"{datetime.now()}: Error when subscribing to webhook: {str(e)}")
    return HttpResponse("Succeed")


def list_webhooks(request):
    try:
        with open(BASE_DIR / "config_data.json", "r") as f:
            local_config_data = json.load(f)
        headers = {
            "Authorization": f"Bearer {local_config_data['access_token']}",
        }
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getWebhooks", headers=headers)
        if 'data' in response.json() and len(response.json()['data']) > 0:
            for webhook in response.json()['data']:
                print(f"The webhook is connected to: {webhook['subscriptionData']}")
                send_message(MANAGER_PHONE_NUMBER, f"The webhook is connected to: {webhook['subscriptionData']}")
    except Exception as e:
        logging.error(f"{datetime.now()}: Error when listing webhooks - {str(e)}")
    return HttpResponse("Succeed")


def delete_webhooks(request):
    with open(BASE_DIR / "config_data.json", "r") as f:
        local_config_data = json.load(f)
    headers = {
        "Authorization": f"Bearer {local_config_data['access_token']}",
    }
    response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getWebhooks", headers=headers)
    if 'data' in response.json() and len(response.json()['data']) > 0:
        webhooks = [webhook['id'] for webhook in response.json()['data']]
        for webhook in webhooks:
            params = {
                "subscriptionID": webhook
            }
            response = requests.delete(f"https://hotels.cloudbeds.com/api/v1.1/deleteWebhook/", headers=headers,
                                       params=params)
            send_message(MANAGER_PHONE_NUMBER, f"Delete webhook with status: {response.json()['success']}")
    return HttpResponse("Succeed")

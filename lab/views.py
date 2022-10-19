from datetime import datetime, timedelta

import requests
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from twilio.rest import Client

from blog.settings import *
from deepl.util import translate
from lab.utils import get_room_type_name, get_room_name, load_access_token, save_access_token, save_refresh_token, \
    load_refresh_token


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
def on_sms_receive(request):  # Get the post QueryDict from the request.
    if request.method == 'POST':
        try:
            data = request.POST
            phone = data['From']
            body = data['Body']
            logging.debug(f"{datetime.now()}: Received message from {phone} with body {body}")
            # Send translation to YuRuan
            message_chinese = translate(body, "ZH")
            send_message(RECEPTIONIST_PHONE_NUMBER, f"{phone}: {body} 翻译：{message_chinese}")
            send_message(phone, "Nous avons reçu votre message, notre personnel vous contactera bientôt.")
            # TODO send message to YuRuan
            # send_message(MANAGER_PHONE_NUMBER, f"""
            # From: {phone}
            #
            #     {body}
            # """)
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
def on_reservation_created(request):
    try:
        # Get the JSON data from the request body
        data = json.loads(request.body)
        reservation_id = data['reservationID']
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getGuest",
                                headers={"Authorization": f"Bearer {load_access_token()}", },
                                params={"reservationID": reservation_id})
        guest_phone = trim_phone(response.json()["data"]["phone"])
        guest_firstname = response.json()["data"]["firstName"]
        guest_lastname = response.json()["data"]["lastName"]
        if data['startDate'] == datetime.now().strftime("%Y-%m-%d") and datetime.now().hour >= 8:
            message = f"""
Bonjour {guest_firstname},

Veuillez donc consulter notre politique d'enregistrement dans le lien suivant avant votre arrivée. https://www.hotelcowansville.ca/en/check-in-policy/
            """
        else:
            message = f"""
Bonjour, {guest_firstname}, votre réservation a été confirmée au {data['startDate']}.
            """
        # send_message(guest_phone, message)
        logging.debug(
            f"{datetime.now()}Sent reservation confirmation message to {guest_firstname} {guest_lastname} at {guest_phone}")

        # send message to remind new guest today
        if data['startDate'] == datetime.now().strftime("%Y-%m-%d") and datetime.now().hour >= 14:
            send_message(RECEPTIONIST_PHONE_NUMBER, f"New upcoming reservation at {datetime.now().strftime('%H:%M')}")

        # send message to adjust price
        params = {
            "startDate": data['startDate'],
            "endDate": data['startDate'],
        }
        results = requests.get("https://hotels.cloudbeds.com/api/v1.1/getRooms",
                               headers={"Authorization": f"Bearer {load_access_token()}"}, params=params)
        rooms = results.json()["data"][0]["rooms"]
        rooms_available = len([room for room in rooms if not room['roomBlocked']])
        send_message(DEVELOPER_PHONE_NUMBER, f"Rooms available: {rooms_available}")
        if rooms_available < 5:
            send_message(RECEPTIONIST_PHONE_NUMBER,
                         f"Only {rooms_available} rooms available on {data['startDate']}, please adjust price.")

    except Exception as e:
        logging.error(f"{datetime.now()} - Error in cloudbeds webhook: " + str(e))
        send_message(DEVELOPER_PHONE_NUMBER, f"Error: {e}")
        return JsonResponse({"Success": False, "Error": str(e)})
    return JsonResponse({"Success": True})


@require_POST
@csrf_exempt
def on_reservation_status_changed(request):
    try:
        data = json.loads(request.body)

        reservation_id = data['reservationID']
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getGuest",
                                headers={"Authorization": f"Bearer {load_access_token()}", },
                                params={"reservationID": reservation_id})
        guest = response.json()["data"]
        guest_phone = trim_phone(guest["phone"])
        if data['status'] == "no_show":

            send_message(
                guest_phone,
                f"""
Bonjour, {guest['firstName']} {guest['lastName']}

Notre système indique que vous ne vous êtes pas enregistré la nuit dernière, nous avons donc marqué votre réservation comme non-présentation. Veuillez noter qu'aucun remboursement ne sera émis pour les réservations de non-présentation.

Hôtel Cowansville
 """)
        elif data['status'] == "canceled":
            send_message(
                guest_phone,
                f"""
Bonjour, {guest['firstName']} {guest['lastName']}

Votre réservation est annulée. Des frais d'annulation peuvent être appliqués selon notre politique d'annulation. Veuillez vous référer à https://hotelcowansville.ca/cancellation-policy pour plus d'informations.

Hôtel Cowansville
""")
        elif data['status'] == "checked_in":
            send_message(
                guest_phone,
                f"""
Bonjour {guest['firstName']}, 

Merci d'avoir choisi l'Hôtel Cowansville.

Veuillez suivre nos règles d'hôtel à https://www.hotelcowansville.ca/hotel-rules.

Votre facture peut être téléchargée sur hotelcowansville.ca/invoice/{reservation_id} à votre date de départ.

N'hésitez pas à répondre à ce message si vous avez des questions.
""")

    except Exception as e:
        logging.error(f"{datetime.now()} - Error in reservation status change webhook: " + str(e))
        return JsonResponse({"Success": False, "Error": str(e)})
    return JsonResponse({"Success": True})


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


@require_POST
@csrf_exempt
def on_reservation_dates_changed(request):
    try:
        data = json.loads(request.body)
        logging.debug(data)
        reservation_id = data['reservationId']
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getGuest",
                                headers={"Authorization": f"Bearer {load_access_token()}", },
                                params={"reservationID": reservation_id})
        guest = response.json()["data"]
        guest_phone = trim_phone(guest["phone"])
        send_message(
            guest_phone,
            f"""
La date de votre réservation a été modifiée.

Arriver: {data['startDate']}
 
Partir: {data['endDate']}
""")
    except Exception as e:
        logging.error(f"{datetime.now()} - Error in reservation dates change webhook: " + str(e))
        return JsonResponse({"Success": False, "Error": str(e)})
    return JsonResponse({"Success": True})


@require_POST
@csrf_exempt
def on_reservation_accommodation_type_changed(request):
    try:
        data = json.loads(request.body)
        logging.debug(data)
        reservation_id = data['reservationId']
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getGuest",
                                headers={"Authorization": f"Bearer {load_access_token()}", },
                                params={"reservationID": reservation_id})
        guest = response.json()["data"]
        guest_phone = trim_phone(guest["phone"])
        room_type_id = data['roomTypeId']
        room_type_name = get_room_type_name(room_type_id)
        logging.debug(f"Your reservation room type has been changed to {room_type_name}")
        send_message(guest_phone, f"Your reservation room type has been changed to {room_type_name}")
    except Exception as e:
        logging.error(f"{datetime.now()} - Error in reservation accommodation type change webhook: " + str(e))
        return JsonResponse({"Success": False, "Error": str(e)})
    return JsonResponse({"Success": True})


# Change room within the same room type
@require_POST
@csrf_exempt
def on_reservation_accommodation_changed(request):
    pass
    # logging.debug(f"on_reservation_accommodation_changed: {request.body}")
    # try:
    #     data = json.loads(request.body)
    #     logging.debug(data)
    #     reservation_id = data['reservationId']
    #     response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getGuest",
    #                             headers={"Authorization": f"Bearer {load_access_token()}", },
    #                             params={"reservationID": reservation_id})
    #     guest = response.json()["data"]
    #     guest_phone = trim_phone(guest["phone"])
    #     room_name = get_room_name(data['roomId'])
    #     logging.debug(f"Your assigned room has been changed. New room number: {room_name}")
    #     send_message(guest_phone, f"Your assigned room has been changed. New room number: {room_name}")
    # except Exception as e:
    #     logging.error(f"{datetime.now()} - Error in reservation accommodation change webhook: " + str(e))
    #     return JsonResponse({"Success": False, "Error": str(e)})
    # return JsonResponse({"Success": True})
    #


def cloudbeds_login(request):
    # send user to cloudbeds login page (oauth), cloudbeds is responsible for redirecting user to callback page
    return redirect(oauth_url)


def cloudbeds_login_redirect(request):
    code = request.GET.get('code')
    codes = exchange_code(request, code)
    save_access_token(codes[0])
    save_refresh_token(codes[1])
    return HttpResponse("Successful")


def try_refresh(request):
    # Refresh access token (should be called before access token is expired, which is 1 hour)
    try:
        refresh()
        return HttpResponse('Access token refreshed')
    except Exception as e:
        return HttpResponse(f'Error in refreshing access token: {e}')


def refresh():
    try:
        data = {
            "grant_type": "refresh_token",
            "client_id": CLOUDBEDS_CLIENT_ID,
            "client_secret": CLOUDBEDS_CLIENT_SECRET,
            "refresh_token": load_refresh_token(),
        }
        header = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post("https://hotels.cloudbeds.com/api/v1.1/access_token", data=data, headers=header)
        credentials = response.json()
        save_access_token(credentials['access_token'])
        save_refresh_token(credentials['refresh_token'])
        logging.info(
            f"New Access token {load_access_token()} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logging.warning(
            f"Error refreshing access token at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Error: {e}. Maybe need to oauth login again because of loss of connection")
        send_message(MANAGER_PHONE_NUMBER,
                     f"Error refreshing access token at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Error: {e}. Maybe need to oauth login again because of loss of connection")


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
    try:
        webhooks_data = [
            {
                "endpointUrl": "https://xunruan.ca/lab/on-reservation-created/",
                "object": "reservation",
                "action": "created"
            },
            {
                "endpointUrl": "https://xunruan.ca/lab/on-reservation-status-changed/",
                "object": "reservation",
                "action": "status_changed"
            },
            {
                "endpointUrl": "https://xunruan.ca/lab/on-reservation-accommodation-type-changed/",
                "object": "reservation",
                "action": "accommodation_type_changed"
            },
            {
                "endpointUrl": "https://xunruan.ca/lab/on-reservation-dates-changed/",
                "object": "reservation",
                "action": "dates_changed"
            },
            {
                "endpointUrl": "https://xunruan.ca/lab/on-reservation-accommodation-changed/",
                "object": "reservation",
                "action": "accommodation_changed"
            }
        ]
        for webhook_data in webhooks_data:
            response = requests.post(
                "https://hotels.cloudbeds.com/api/v1.1/postWebhook",
                headers={"Authorization": f"Bearer {load_access_token()}"},
                data=webhook_data
            )

            if response.status_code != 200:
                logging.warning(f"Error subscribing to webhook at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                send_message(MANAGER_PHONE_NUMBER, "Error subscribing to webhook")
                return HttpResponse("Error subscribing to webhook")

        logging.debug(f"xun - {len(webhooks_data)} Webhook subscription successful")
    except Exception as e:
        print(e)
        logging.error(f"{datetime.now()}: Error when subscribing to webhook: {str(e)}")
    return HttpResponse("Succeed")


def list_webhooks(request):
    print("list webhooks")
    try:
        headers = {
            "Authorization": f"Bearer {load_access_token()}",
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
    print("delete")
    headers = {
        "Authorization": f"Bearer {load_access_token()}",
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

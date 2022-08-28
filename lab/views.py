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
def twilio_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.POST['Body'])
            logging.debug(data)
            # phone = data['From']
            # body = data['Body']
            # logging.debug(f"{datetime.now()}: Received message from {phone} with body {body}")
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
            send_message(cell_phone,
                         f"""
 Bonjour, {guest_firstname}!
 Votre réservation a été confirmée.
 Si vous avez des questions, veuillez nous envoyer un courriel à info@cowansvillehotel.com.
                         """)
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


def get_checkout_rooms_tomorrow():
    with open(BASE_DIR / "config_data.json", "r") as f:
        local_config_data = json.load(f)
    try:
        headers = {
            "Authorization": f"Bearer {local_config_data['access_token']}",
        }
        params = {
            "checkOutFrom": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "checkOutTo": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "includeGuestsDetails": True,
        }

        response_for_guest_checkout = requests.get(
            "https://hotels.cloudbeds.com/api/v1.1/getReservations",
            headers=headers,
            params=params)
        reservations_filtered = [data for data in response_for_guest_checkout.json()['data'] if
                                 data['status'] not in ['canceled', 'no_show']]

        rooms = [reservation['guestList'] for reservation in reservations_filtered]
        checkout_room_ids = []

        for room in rooms:
            for k, v in room.items():
                for guest_room in v['rooms']:
                    checkout_room_ids.append(guest_room['roomName'])
        return checkout_room_ids
    except Exception as e:
        send_message(MANAGER_PHONE_NUMBER, "Error getting checkout rooms: " + str(e))
        return []


def send_housekeeper_night_message():
    with open(BASE_DIR / "config_data.json", "r") as f:
        local_config_data = json.load(f)
    try:
        headers = {
            "Authorization": f"Bearer {local_config_data['access_token']}",
        }
        params = {
            "checkOutFrom": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "checkOutTo": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "includeGuestsDetails": True,
        }

        response_for_guest_checkout = requests.get(
            "https://hotels.cloudbeds.com/api/v1.1/getReservations",
            headers=headers,
            params=params)
        reservations_filtered = [data for data in response_for_guest_checkout.json()['data'] if
                                 data['status'] not in ['canceled', 'no_show']]

        rooms = [reservation['guestList'] for reservation in reservations_filtered]
        checkout_room_ids = []

        for room in rooms:
            for k, v in room.items():
                for guest_room in v['rooms']:
                    checkout_room_ids.append(guest_room['roomName'])

        checkin_params = {
            "checkInFrom": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "checkInTo": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "includeGuestsDetails": True,
        }

        response_for_guest_checkin = requests.get(
            "https://hotels.cloudbeds.com/api/v1.1/getReservations",
            headers=headers,
            params=checkin_params)
        reservations_filtered = [data for data in response_for_guest_checkin.json()['data'] if
                                 data['status'] not in ['canceled']]

        rooms = [reservation['guestList'] for reservation in reservations_filtered]
        checkin_room_ids = []

        for room in rooms:
            for k, v in room.items():
                for guest_room in v['rooms']:
                    checkin_room_ids.append(guest_room['roomName'])

        must_do_rooms = []
        for checkout_room_id in checkout_room_ids:
            if checkout_room_id in checkin_room_ids:
                must_do_rooms.append(checkout_room_id)

        send_message(phone_number='+15794202983',
                     message=
                     f"""
        Tomorrow, there are {len(set(checkout_room_ids))} rooms to be checked out.
        And {len(set(must_do_rooms))} rooms that needs to be checked out and has someone check-in.
        they are {set(must_do_rooms)}
        """)
    except Exception as e:
        send_message(phone_number='+15794202983', message=f"Error: {e}")


def send_checkin_procedure():
    with open(BASE_DIR / "config_data.json", "r") as f:
        local_config_data = json.load(f)
    try:
        # This should run every day at 9 am.
        headers = {
            "Authorization": f"Bearer {local_config_data['access_token']}",
        }
        params = {
            "checkInFrom": datetime.now().strftime("%Y-%m-%d"),
            "checkInTo": datetime.now().strftime("%Y-%m-%d"),
            "includeGuestInfo": True,
        }
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getGuestList", headers=headers, params=params)
        datas = response.json()['data']
        datas = [data for data in datas if data["status"] == "confirmed"]
        guests_info = [(data["guestName"], trim_phone(data["guestPhone"]), data["reservationID"], data['status']) for
                       data
                       in datas]

        for guest in guests_info:
            if guest[1] is None:
                print("Invalid phone number for guest:", guest[0])
                continue

            message = f"""
Bonjour {guest[0].split(" ")[0]},
-- Vous avez une réservation à l'Hôtel Cowansville pour aujourd'hui.
-- Veuillez vous enregistrer après 15h30. Nous avons un personnel limité pour nettoyer les chambres, donc tout enregistrement anticipé avant 15h00 sera refusé.
-- Votre clé sera prête pour vous à la réception pour un enregistrement plus rapide si nous avons bien reçu votre paiement.
"""
            send_message(guest[1], message)
            logging.info(f"{datetime.now()}: Checkin procedure sent to {guest[0]} at {guest[1]}")
    except Exception as e:
        logging.error(f"Error sending checkin procedure: {e}")


def send_review_request():
    with open(BASE_DIR / "config_data.json", "r") as f:
        local_config_data = json.load(f)
    try:
        headers = {
            "Authorization": f"Bearer {local_config_data['access_token']}",
        }
        params = {
            "checkOutFrom": datetime.now().strftime("%Y-%m-%d"),
            "checkOutTo": datetime.now().strftime("%Y-%m-%d"),
            "includeGuestsDetails": True,
        }
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getReservations", headers=headers, params=params)
        datas = response.json()['data']
        datas = [data for data in datas if data["status"] not in ("no_show", "canceled")]
        for data in datas:
            source_name = data['sourceName']
            guest_detail = data['guestList'][data['guestID']]
            guest_name = guest_detail['guestName']
            guest_phone = trim_phone(guest_detail['guestPhone'])
            guest_email = guest_detail['guestEmail']
            if DEBUG:
                print(f"{guest_name} reserves on {source_name}")
            if source_name in ("Website/Booking Engine", "Phone", "Walk-In"):
                message = f"""
    Bonjour {guest_name.split(" ")[0]},
    J'espère que vous passerez un excellent séjour à l'Hôtel Cowansville.
    Pouvez-vous prendre un moment pour laisser un bon avis sur le lien: https://g.page/r/CTrNBv9O-L4_EAg/review ?
    Votre gentillesse nous aidera à vous fournir le meilleur service à l'avenir.
                """
                send_message(guest_phone, message)
            else:
                message = f"""
    Bonjour {guest_name.split(" ")[0]},
    J'espère que vous passerez un excellent séjour à l'Hôtel Cowansville.
    Pouvez-vous prendre une seconde pour nous faire un commentaire sur {source_name} ?
    Vous courez la chance de gagner une remise en argent de 10 $, et votre avis nous aidera à traverser la période post-COVID.
    Si vous souhaitez nous revoir à l'avenir, je vous recommande de réserver directement sur cowansvillehotel.com pour notre meilleur prix.
                    """
                if DEBUG:
                    print("Sending one review request...")
                send_message(guest_phone, message)
        if DEBUG:
            print(f"Send review request to {len(datas)} guests")
        logging.info(f"Review request sent to guest successfully at {datetime.now()}")
    except Exception as e:
        logging.error(f"Error sending review request: {e} at {datetime.now()}")


def send_checkout_procedure():
    with open(BASE_DIR / "config_data.json", "r") as f:
        local_config_data = json.load(f)
    try:
        headers = {
            "Authorization": f"Bearer {local_config_data['access_token']}",
        }
        params = {
            "checkOutFrom": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "checkOutTo": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "includeGuestsDetails": True,
        }
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getReservations", headers=headers, params=params)
        datas = response.json()['data']
        datas = [data for data in datas if data["status"] not in ("no_show", "canceled")]
        body_message = f"""
    J'espère que vous passerez un excellent séjour à l'Hôtel Cowansville.
    Ce message est un rappel que votre départ est à 11h demain matin.
    Lorsque vous êtes prêt à partir, assurez-vous de ne rien oublier dans la chambre et laissez votre clé dans votre chambre
    Si vous avez besoin d'un reçu, veuillez envoyer un courriel à info@cowansvillehotel.com
    Nous espérons vous voir la prochaine fois.
            """
        for data in datas:
            source_name = data['sourceName']
            guest_detail = data['guestList'][data['guestID']]
            guest_name = guest_detail['guestName']
            guest_phone = trim_phone(guest_detail['guestPhone'])
            if DEBUG:
                print(f"{guest_name} reserves on {source_name}")
            title = f"Bonjour {guest_name.split()[0]}\n"
            send_message(guest_phone, title + body_message)
        logging.info("Checkout procedure sent to guest successfully.")
    except Exception as e:
        logging.error(f"Error when sending checkout procedure to guests: {str(e)} at {datetime.now()}")


def send_housekeeping_notice_to_guest():
    with open(BASE_DIR / "config_data.json", "r") as f:
        local_config_data = json.load(f)
    try:
        headers = {
            "Authorization": f"Bearer {local_config_data['access_token']}",
        }
        # Get guests and check-in in the past, and check-out in the future. (means they are in-house)
        params = {
            "checkInTo": (datetime.now()).strftime("%Y-%m-%d"),
            "checkOutFrom": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "includeGuestInfo": True,
        }
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getGuestList", headers=headers, params=params)
        datas = response.json()['data']
        datas = [data for data in datas if data["status"] not in ("canceled", "no_show")]
        room_number_to_clean = get_checkout_rooms_tomorrow()
        if len(room_number_to_clean) > 12:
            main_body_message = f"""
- Demain, nous connaîtrons une pénurie de personnel et de serviettes propres car nous sommes surchargés de chambres à nettoyer. Nous nous excusons de ne pas pouvoir faire de ménage.

- Notre heure calme est de 23h00 à 7h00. Veuillez garder le silence lorsque vous marchez dans le couloir et baissez la voix dans la pièce.
            """
            send_message("Don't do housekeeping tomorrow, room:", room_number_to_clean)
        else:
            main_body_message = f"""
- service exclusif : changement d'approvisionnement quotidien (10$ une fois)
    Si vous avez besoin de nous pour changer des fournitures telles que des sacs poubelles ou des serviettes, veuillez accrocher la plaque de ménage à l'extérieur de votre chambre sur la poignée de la porte avant 10h00 tous les jours pendant votre séjour.

- Notre heure calme est de 23h00 à 7h00. Veuillez garder le silence lorsque vous marchez dans le couloir et baissez la voix dans la pièce. 
"""
        for each_guest in datas:
            guest_name = each_guest['guestName']
            guest_phone = trim_phone(each_guest['guestPhone'])
            title_message = f"Bonjour {guest_name.split()[0]},\n"
            send_message(guest_phone, title_message + main_body_message)
        logging.info(f"Housekeeping notice sent to guest. Room: {room_number_to_clean} at {datetime.now()}")
    except Exception as e:
        logging.error(f"Error when sending housekeeping notice to guests: {str(e)} at {datetime.now()}")


def send_daily_summary():
    with open(BASE_DIR / "config_data.json", "r") as f:
        local_config_data = json.load(f)
    try:
        headers = {
            "Authorization": f"Bearer {local_config_data['access_token']}",
        }
        # Get guests and check-in in the past, and check-out in the future. (means they are in-house)
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getDashboard", headers=headers)

        data = response.json()['data']
        message = f"""
        今天报告：{datetime.now().strftime("%Y-%m-%d")}
        房数: {data['roomsOccupied']}
        入住率: {data['percentageOccupied']}%
        新入住数量: {data['arrivals']}
        退房数量: {data['departures']}
        连住房数: {data['inHouse']}
        """
        send_message(MANAGER_PHONE_NUMBER, message)
        logging.info(f"{datetime.now()} Send daily summary to {MANAGER_PHONE_NUMBER}")
    except Exception as e:
        logging.warning(f"{datetime.now()} Error when sending daily summary: {str(e)}")


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

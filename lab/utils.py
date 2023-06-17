import logging
from datetime import datetime

import requests
from django.http import JsonResponse

from blog.settings import BASE_DIR


def get_room_type_name(room_type_id):
    try:
        headers = {
            'Authorization': f"Bearer {load_access_token()}",
        }
        params = {
            "roomTypeIDs": str(room_type_id),
        }
        response = requests.get(
            "https://hotels.cloudbeds.com/api/v1.1/getRoomTypes",
            headers=headers,
            params=params,
        )
        room_type_name = response.json()['data'][0]['roomTypeName']
    except Exception as e:
        logging.error(f"{datetime.now()} - Xun - get_room_type_name fail - {e}")
        return None
    return room_type_name


def get_room_name(room_id):
    headers = {
        'Authorization': f"Bearer {load_access_token()}",
    }
    response = requests.get(
        "https://hotels.cloudbeds.com/api/v1.1/getRooms",
        headers=headers,
    )
    if not response.ok:
        return None
    rooms = response.json()['data'][0]['rooms']
    for room in rooms:
        if room['roomID'] == room_id:
            return room['roomName']
    return None


# Token Management
def load_access_token():
    with open(BASE_DIR / "access_token.txt", "r") as f:
        access_token = f.read()
        return access_token


def save_access_token(access_token):
    with open(BASE_DIR / "access_token.txt", "w") as f:
        f.write(access_token)


def load_refresh_token():
    with open(BASE_DIR / "refresh_token.txt", "r") as f:
        refresh_token = f.read()
        return refresh_token


def save_refresh_token(refresh_token):
    with open(BASE_DIR / "refresh_token.txt", "w") as f:
        f.write(refresh_token)

def get_reservation_by_id(reservation_id):
    # Return the reservation data object
    response = requests.get(
        "https://hotels.cloudbeds.com/api/v1.1/getGuest",
        headers={'Authorization': f'Bearer {load_access_token()}'},
        params={"reservationID": reservation_id}
    )
    if not response.ok:
        return None
    return response.json()['data']
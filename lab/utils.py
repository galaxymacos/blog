import logging
from datetime import datetime

import requests
from django.http import JsonResponse

from blog.settings import CONFIG_DATA


def get_room_type_name(room_type_id):
    try:
        headers = {
            'Authorization': f"Bearer {CONFIG_DATA['access_token']}",
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
        'Authorization': f"Bearer {CONFIG_DATA['access_token']}",
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

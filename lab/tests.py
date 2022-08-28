import json
import webbrowser
from datetime import datetime

import requests
from django.test import TestCase
from django.urls import reverse

from blog.settings import BASE_DIR
from lab.views import trim_phone


# Create your tests here.
class CloudbedsConnectionTestCase(TestCase):
    def setUp(self) -> None:
        print("setUp")
        # Need OAuth
        pass

    def test_get_in_house_guest(self):
        with open(BASE_DIR / "config_data.json", "r") as f:
            local_config_data = json.load(f)

        headers = {
            "Authorization": f"Bearer {local_config_data['access_token']}",
        }
        params = {
            "checkInTo": datetime.now().strftime("%Y-%m-%d"),
            "checkOutFrom": datetime.now().strftime("%Y-%m-%d"),
            "excludeSecondaryGuests": True,
            "includeGuestInfo": True,
        }
        response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getGuestList", headers=headers, params=params)
        data = response.json()["data"]

        guest_dict = {}
        for guest in data:
            if guest['guestName'] not in guest_dict:
                guest_dict[guest['guestName']] = trim_phone(guest['guestPhone'])
        for guest_name, guest_phone in guest_dict.items():
            pass
            # print(f"{guest_name} - {guest_phone} is in room")

        self.assertEqual(response.status_code, 200)

    # def test_reservation_api(self):
    #     pass
    #     with open(BASE_DIR / "config_data.json", "r") as f:
    #         local_config_data = json.load(f)
    #
    #     headers = {
    #         "Authorization": f"Bearer {local_config_data['access_token']}",
    #     }
    #     params = {
    #         "status": "checked_in",
    #         "includeGuestsDetails": True,
    #     }
    #     response = requests.get("https://hotels.cloudbeds.com/api/v1.1/getReservations", headers=headers,params=params)
    #     data = response.json()["data"]
    #     for reservation in data:
    #
    #     self.assertEqual(response.status_code, 200)

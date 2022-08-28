import requests
from django.test import TestCase


# Create your tests here.
class DeeplTestCase(TestCase):

    def test_url(self):
        params = {
            'auth_key': '904de63a-2caf-e1a0-dce2-95562021f7cc:fx',
            'text': 'Hello World!',
            'target_lang': 'FR',
        }
        response = requests.get('https://api-free.deepl.com/v2/translate', params=params)
        print(response.json())
        self.assertEqual(response.status_code, 200)

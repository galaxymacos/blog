import requests
from django.http import JsonResponse


# Create your views here.
def index(request):
    params = {
        'auth_key': '904de63a-2caf-e1a0-dce2-95562021f7cc:fx',
        'text': 'Hello World!',
        'target_lang': 'FR',
    }
    response = requests.get('https://api-free.deepl.com/v2/translate', params=params)
    print(response.status_code)
    # print(response.json()["translations"][0]["text"])
    return JsonResponse(response.json())

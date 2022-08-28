import requests
from django.http import JsonResponse

from blog.settings import env


# Create your views here.
def index(request):
    params = {
        'auth_key': env("DEEPL_AUTH_KEY"),
        'text': 'Hello World!',
        'target_lang': 'FR',
    }
    response = requests.get('https://api-free.deepl.com/v2/translate', params=params)
    print(response.status_code)
    # print(response.json()["translations"][0]["text"])
    return JsonResponse(response.json())

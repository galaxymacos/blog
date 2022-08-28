import requests

from blog.settings import env


def translate(text, target_lang):
    params = {
        'auth_key': env("DEEPL_AUTH_KEY"),
        'text': text,
        'target_lang': target_lang,
    }
    response = requests.get('https://api-free.deepl.com/v2/translate', params=params)
    return response.json()["translations"][0]["text"]
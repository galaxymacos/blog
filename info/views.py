from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext, activate, get_language


# Create your views here.
def index(request):
    hello_text = translate(language='fr')
    return render(request, 'index.html', {'hello_text': gettext("Hello World!")})


def translate(language):
    cur_language = get_language()
    try:
        activate(language)  # Activate new language
        text = gettext('Hello World!')  # try to translate the text in the new language
    finally:
        activate(cur_language)
    return text

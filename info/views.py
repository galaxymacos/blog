from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext


# Create your views here.
def index(request):
    hello_text = gettext('Hello World!')
    return render(request, 'index.html', {'hello_text': hello_text})

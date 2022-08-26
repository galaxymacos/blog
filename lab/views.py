from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


# Create your views here.

@csrf_exempt
def twilio_webhook(request):
    if request.method == 'POST':
        return HttpResponse("Twilio webhook: POST received")
    else:
        return HttpResponse("Twilio webhook: GET received")


@csrf_exempt
def cloudbeds_webhook(request):
    # log
    if request.method == "POST":
        return HttpResponse("Cloudbeds webhook: POST received")
    else:
        return HttpResponse("Cloudbeds webhook: GET received")

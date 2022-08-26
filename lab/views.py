import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging


# Create your views here.

@csrf_exempt
def twilio_webhook(request):
    logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
    if request.method == 'POST':
        logging.debug("Twilio webhook: POST received")
        return HttpResponse("Twilio webhook: POST received")
    else:
        logging.debug("Twilio webhook: GET received")
        return HttpResponse("Twilio webhook: GET received")


@csrf_exempt
def cloudbeds_webhook(request):
    logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
    if request.method == "POST":
        try:
            logging.debug("Cloudbeds webhook: POST received")
            logging.debug(request.POST['Body'])
        except Exception as e:
            logging.debug(e)
            logging.debug("Error parsing JSON")
        return HttpResponse("Cloudbeds webhook: POST received")
    else:
        logging.debug("Cloudbeds webhook: GET received")
        return HttpResponse("Cloudbeds webhook: GET received")

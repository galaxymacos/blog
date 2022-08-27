import logging
from datetime import datetime

from django.core.management import BaseCommand

from lab.views import send_checkout_procedure


class Command(BaseCommand):
    # Trigger every morning at 10 pm
    def handle(self, *args, **options):
        logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
        logging.debug('Send checkout procedure at {}'.format(datetime.now()))
        send_checkout_procedure()
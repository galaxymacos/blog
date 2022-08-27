import logging
from datetime import datetime

from django.core.management import BaseCommand

from lab.views import send_checkout_procedure


class Command(BaseCommand):
    # Trigger every morning at 10 pm
    def handle(self, *args, **options):
        logging.info('Send checkout procedure at {}'.format(datetime.now()))
        send_checkout_procedure()
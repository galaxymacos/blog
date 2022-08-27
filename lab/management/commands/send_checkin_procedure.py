import logging
from datetime import datetime

from django.core.management import BaseCommand

from lab.views import send_checkin_procedure


class Command(BaseCommand):
    # Trigger every morning at 10 am
    def handle(self, *args, **options):
        logging.info('Send check-in procedure at {}'.format(datetime.now()))
        send_checkin_procedure()
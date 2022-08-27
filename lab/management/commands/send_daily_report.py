import logging
from datetime import datetime

from django.core.management import BaseCommand

from lab.views import send_daily_summary


class Command(BaseCommand):
    # Trigger every night at 11 pm
    def handle(self, *args, **options):
        logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
        logging.debug('Ready to send daily summary at {}'.format(datetime.now()))
        send_daily_summary()

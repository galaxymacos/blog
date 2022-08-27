import logging
from datetime import datetime

from django.core.management import BaseCommand

from lab.views import send_housekeeping_notice_to_guest


class Command(BaseCommand):
    # Trigger every day at 10 pm
    def handle(self, *args, **options):
        logging.info('Ready to send housekeeping notice to guest at {}'.format(datetime.now()))
        send_housekeeping_notice_to_guest()

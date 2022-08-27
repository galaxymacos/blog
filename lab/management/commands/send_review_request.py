import logging
from datetime import datetime

from django.core.management import BaseCommand

from lab.views import send_review_request


class Command(BaseCommand):
    # Trigger every night at 9 pm
    def handle(self, *args, **options):
        logging.info('Ready to send review request at {}'.format(datetime.now()))
        send_review_request()

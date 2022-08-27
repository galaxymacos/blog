import logging
from datetime import datetime

from django.core.management import BaseCommand

from lab.views import send_review_request


class Command(BaseCommand):
    # Trigger every night at 9 pm
    def handle(self, *args, **options):
        logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
        logging.debug('Ready to send review request at {}'.format(datetime.now()))
        send_review_request()
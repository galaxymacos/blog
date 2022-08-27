import logging
from datetime import datetime

from django.core.management import BaseCommand

from lab.views import refresh


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
        logging.debug('refresh started at {}'.format(datetime.now()))
        refresh()

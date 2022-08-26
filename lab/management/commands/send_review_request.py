from django.core.management import BaseCommand

from lab.views import send_review_request


class Command(BaseCommand):
    # Trigger every night at 9 pm
    def handle(self, *args, **options):
        send_review_request()
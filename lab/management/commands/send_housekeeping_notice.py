from django.core.management import BaseCommand

from lab.views import send_housekeeping_notice_to_guest


class Command(BaseCommand):
    # Trigger every day at 10 pm
    def handle(self, *args, **options):
        send_housekeeping_notice_to_guest()

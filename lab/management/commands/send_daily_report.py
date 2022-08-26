from django.core.management import BaseCommand

from lab.views import send_daily_summary


class Command(BaseCommand):
    # Trigger every night at 11 pm
    def handle(self, *args, **options):
        send_daily_summary()

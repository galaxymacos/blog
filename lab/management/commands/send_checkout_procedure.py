from django.core.management import BaseCommand

from lab.views import send_checkout_procedure


class Command(BaseCommand):
    # Trigger every morning at 10 pm
    def handle(self, *args, **options):
        send_checkout_procedure()
from django.core.management import BaseCommand

from lab.views import refresh


class Command(BaseCommand):
    def handle(self, *args, **options):
        refresh()

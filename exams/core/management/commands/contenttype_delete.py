from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, **options):
        ContentType.objects.all().delete()

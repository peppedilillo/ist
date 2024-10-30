from django.core.management.base import BaseCommand

from app.models import Board
from app.models import Keyword


class Command(BaseCommand):
    help = "Adds keywords and boards"

    def handle(self, *args, **options):
        for choice in Keyword.Keywords:
            Keyword.objects.get_or_create(name=choice.value)

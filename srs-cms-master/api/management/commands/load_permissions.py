from django.core.management.base import BaseCommand
from api.common import Permissions


class Command(BaseCommand):
    help = "Import Permissions and User Groups."

    def handle(self, *args, **kwargs):
        Permissions._create()

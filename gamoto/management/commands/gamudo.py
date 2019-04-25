from django.core.management.base import BaseCommand

import os


class Command(BaseCommand):
    help = 'Make a shell'

    def handle(self, *args, **options):
        os.system('bash')

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Set a user as admin'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1, type=str)

    def handle(self, *args, **options):
        username = options['username'][0]
        u = User.objects.get(username=username)
        u.is_superuser = True
        u.is_staff = True
        u.save()

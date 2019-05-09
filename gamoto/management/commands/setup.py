from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.conf import settings
# from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from gamoto import ca, users

import os
import sys


class Command(BaseCommand):
    help = 'Configure the CA'

    def handle(self, *args, **options):
        def _status(var):
            if var:
                self.stdout.write(self.style.SUCCESS('OK'))
            else:
                self.stdout.write(self.style.SUCCESS('EXISTS'))

        if (users.getSystemUID() != os.getuid()):
            self.stdout.write(self.style.ERROR(
                "Please run this command as root, or " + settings.GAMOTO_USER))
            sys.exit(1)

        # Ensure paths exist
        for path in [settings.BASE_PATH, settings.CA_PATH, settings.USER_PATH]:
            if not os.path.isdir(path):
                os.makedirs(path)

        # Setup CA
        myca = ca.CertificateAuthority(
            settings.CA_SETUP['ou'],
            settings.CA_SETUP['org'],
            settings.CA_SETUP['email'],
            settings.CA_SETUP['country'],
            settings.CA_SETUP['state'],
            settings.CA_SETUP['city'],
            key_path=settings.CA_PATH
        )

        self.stdout.write("Creating Diffie-Hellman parameters... ", ending="")
        self.stdout.flush()
        _status(myca.createDH())

        self.stdout.write("Building certificate authority... ", ending="")
        self.stdout.flush()
        _status(myca.createCA('openvpn'))

        self.stdout.write("Creating server certificate request... ", ending="")
        self.stdout.flush()
        _status(myca.createCSR('openvpn'))

        self.stdout.write("Signing server certificate... ", ending="")
        self.stdout.flush()
        _status(myca.signCSR('openvpn', server=True))

        self.stdout.write("Generating CRL... ", ending="")
        self.stdout.flush()
        _status(myca.createCRL())

        # Setup DB
        self.stdout.write("Creating types and permissions... ", ending="")
        self.stdout.flush()
        try:
            ctype = ContentType.objects.create(
                app_label='subnet',
                model='group'
            )
            ctype.save()
            _status(True)
        except IntegrityError:
            _status(False)

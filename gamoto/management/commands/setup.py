from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.db.utils import IntegrityError
from django.conf import settings

from gamoto import ca, users

import os
import sys


class Command(BaseCommand):
    help = 'Configure the CA'

    def _status(self, var):
        if var:
            self.stdout.write(self.style.SUCCESS('OK'))
        else:
            self.stdout.write(self.style.SUCCESS('EXISTS'))

    def configureDB(self):
        # Setup DB
        self.stdout.write("Creating content types... ", ending="")
        self.stdout.flush()
        try:
            ctype = ContentType.objects.create(
                app_label='subnet',
                model='group'
            )
            ctype.save()
            self._status(True)
        except IntegrityError:
            self._status(False)

        self.stdout.write("Creating permissions... ", ending="")
        self.stdout.flush()
        try:
            ctype = ContentType.objects.get(app_label='auth', model='permission')
            default_perm = Permission.objects.create(
                content_type=ctype,
                name='Default Group',
                codename='default_group'
            )
            default_perm.save()
            self._status(True)
        except IntegrityError:
            self._status(False)

    def configureCA(self):
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
        self._status(myca.createDH())

        self.stdout.write("Building certificate authority... ", ending="")
        self.stdout.flush()
        self._status(myca.createCA('openvpn'))

        self.stdout.write("Creating server certificate request... ", ending="")
        self.stdout.flush()
        self._status(myca.createCSR('openvpn'))

        self.stdout.write("Signing server certificate... ", ending="")
        self.stdout.flush()
        self._status(myca.signCSR('openvpn', server=True))

        self.stdout.write("Generating CRL... ", ending="")
        self.stdout.flush()
        self._status(myca.createCRL())

    def handle(self, *args, **options):
        if (users.getSystemUID() != os.getuid()):
            self.stdout.write(self.style.ERROR(
                "Please run this command as root, or " + settings.GAMOTO_USER))
            sys.exit(1)

        self.configureCA()
        self.configureDB()


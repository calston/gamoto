from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from gamoto import ca, users

import os


class Command(BaseCommand):
    help = 'Configure the CA'

    def handle(self, *args, **options):
        def _status(var):
            if var:
                self.stdout.write(self.style.SUCCESS('OK'))
            else:
                self.stdout.write(self.style.SUCCESS('EXISTS'))

        uid = users.getSystemUID()
        my_uid = os.getuid()
        if (my_uid == 0):
            os.setuid(uid)

        elif (my_uid != uid):
            self.stdout.write(self.style.ERROR(
                "Please run this command as root, or " + settings.GAMOTO_USER))
            return

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

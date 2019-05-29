from django.core.management.base import BaseCommand

from django.conf import settings
from django.contrib.auth.models import User

from gamoto import users, openvpn, iptables

import os
import sys


class Command(BaseCommand):
    help = 'OpenVPN client-connect scripts'

    def __init__(self, *a, **kw):
        BaseCommand.__init__(self, *a, **kw)

        self.ipt = iptables.IPTables()

    def add_arguments(self, parser):
        parser.add_argument('client_cmd_path', nargs='?', type=str)

    def connect(self, user):
        u = User.objects.get(username=user)

        if not u.is_active:
            self.stderr.write('User '+user+' disabled\n')
            sys.exit(1)

        if settings.MANAGE_IPTABLES:
            self.ipt.flushClient(user)
            subnets = openvpn.getRoutes(user)

            if subnets:
                ip = os.getenv('ifconfig_pool_remote_ip')
                for subnet in subnets:
                    self.ipt.allowClient(user, ip, subnet)

    def disconnect(self, user):
        if settings.MANAGE_IPTABLES:
            self.ipt.flushClient(user)

    def handle(self, *args, **options):
        script_type = os.getenv('script_type')
        user = os.getenv('common_name')
        if not user:
            self.stderr.write(
                'Error, no CN found. This script must be run by OpenVPN!')
            sys.exit(1)

        if settings.MANAGE_IPTABLES:
            self.ipt.setupIptables()

        if script_type == 'client-connect':
            self.connect(user)

        elif script_type == 'client-disconnect':
            self.disconnect(user)

        else:
            self.stderr.write('Not sure what you want me to do :(')
            sys.exit(1)

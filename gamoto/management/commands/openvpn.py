from django.core.management.base import BaseCommand

from django.conf import settings
from django.contrib.auth.models import User

from gamoto import users, openvpn

import os
import sys


class Command(BaseCommand):
    help = 'OpenVPN client-connect scripts'

    def add_arguments(self, parser):
        parser.add_argument('client_cmd_path', nargs='?', type=str)

    def getIptables(self):
        result, err = users.sudo('iptables-save')
        result = result.strip()
        rules = [i for i in result.decode().split('\n')
                 if not i.startswith('#')]

        tables = {}
        table = None
        for r in rules:
            if r.startswith('*'):
                table = r.strip('*')
                tables[table] = {}
            elif r.startswith(':'):
                chain, default, b = r.strip(':').split()
                if default == '-':
                    default = None

                tables[table][chain] = {
                    'default': default,
                    'rules': []
                }
            elif r.startswith('-'):
                token, chain, args = r.split(None, 2)
                tables[table][chain]['rules'].append(args)
        return tables

    def iptables(self, rule):
        result, err = users.sudo('/sbin/iptables', *rule.split())
        if err:
            raise Exception(err)

    def setupIptables(self):
        # Makes sure iptables has our chain
        ipt = self.getIptables()
        print(ipt.get('filter', []))
        if 'openvpn' not in ipt.get('filter', []):
            print('Create table')
            self.iptables('-N openvpn')

        jump_rule = '-i %s -j openvpn' % settings.VPN_INTERFACE

        input_rules = ipt.get('filter', {}).get('INPUT', {}).get('rules', [])

        if jump_rule not in input_rules:
            self.iptables('-I INPUT 1 -i tun0 -j openvpn')

    def allowClient(self, name, src, dest):
        if not (name and src and dest):
            return None

        rules = self.getIptables()['filter']['openvpn']['rules']

        rule = '-A openvpn -i tun0 -s %s -d %s -m comment --comment "%s"' % (
            src, dest, name
        )

        if rule not in rules:
            self.iptables(rule)

    def flushClient(self, name):
        rules = self.getIptables()['filter']['openvpn']['rules']
        for i, r in enumerate(rules):
            idx = str(i + 1)
            if name in r.split()[-1]:
                users.sudo('/sbin/iptables', '-D', 'openvpn', idx)

    def connect(self, user):
        subnets = openvpn.getRoutes(user)
        ip = os.getenv('ifconfig_pool_remote_ip')
        self.setupIptables()

        for subnet in subnets:
            self.allowClient(user, ip, subnet)

    def disconnect(self, user):
        self.flushClient(user)

    def handle(self, *args, **options):
        script_type = os.getenv('script_type')
        user = os.getenv('common_name')
        if not user:
            self.stderr.write(
                'Error, no CN found. This script must be run by OpenVPN!')
            sys.exit(1)

        if settings.MANAGE_IPTABLES:
            if script_type == 'client-connect':
                self.connect(user)

            elif script_type == 'client-disconnect':
                self.disconnect(user)

            else:
                self.stderr.write('Not sure what you want me to do :(')
                sys.exit(1)

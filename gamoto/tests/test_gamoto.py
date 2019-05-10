from django.test import TestCase, Client
from django.urls import reverse, exceptions
from django.urls.resolvers import URLPattern
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from gamoto.tests import data

import os


# Create your tests here.
class TestRockFace(TestCase):
    def test_authentication_required(self):
        from gamoto import urls

        redirect_map = []
        for url in urls.urlpatterns:
            if not isinstance(url, URLPattern):
                continue
            if url.name == "login":
                continue
            try:
                urlr = reverse(url.name)
                redirect_map.append((url.name, urlr))
            except exceptions.NoReverseMatch:
                pass

        for name, path in redirect_map:
            r = self.client.get(reverse(name))
            self.assertRedirects(r, reverse('login')+'?next=' + path)

    def test_login(self):
        self.client.login(username='test', password='test')


class TestOpenvpn(TestCase):
    def setUp(self):
        self.sudo_commands = []
        self.blank_ipt = False

        self.ipt_copy = [i for i in data.IPTABLES_SAVE]

        ctype = ContentType.objects.create(
            app_label='subnet',
            model='group'
        )

        group = Group.objects.create(name="testgroup")

        user = User.objects.create(username="test", email="test@mail.com")
        user.groups.add(group)

        perm = Permission.objects.create(
            codename="network_10.1.2.0/24",
            name="My network",
            content_type=ctype
        )

        group.permissions.add(perm)

    def tearDown(self):
        data.IPTABLES_SAVE = self.ipt_copy

    def _fake_sudo(self, *a):
        self.sudo_commands.append(' '.join(a))
        result = b''
        if 'iptables-save' in a:
            if self.blank_ipt:
                result = b'\n'
            else:
                result = bytes('\n'.join(data.IPTABLES_SAVE), encoding='ascii')

        elif a[1] == '-N':
            data.IPTABLES_SAVE.insert(5, ":%s - [0:0]" % a[2])

        elif a[1] == '-A':
            data.IPTABLES_SAVE.insert(6, ' '.join(a[1:]))

        return (result, b'')

    def _fake_get_user(self, name):
        return {
            'name': name,
            'uid': 1001,
            'gid': 1001,
            'gecos': name.capitalize,
            'home': '/var/lib/gamoto/users' + name,
            'shell': '/bin/false',
            'mfa': True
        }

    def test_blank_iptables(self):
        # For dumb reasons iptables-save can return nothing
        from gamoto.management.commands import openvpn
        from gamoto import users

        openvpn.users.sudo = self._fake_sudo
        openvpn.users.getUser = self._fake_get_user

        self.blank_ipt = True

        cmd = openvpn.Command()

        tables = cmd.getIptables()

        cmd.setupIptables()

        tables = cmd.getIptables()

        self.blank_ipt = False

        self.assertListEqual(self.sudo_commands, [
            'iptables-save',
            'iptables-save',
            '/sbin/iptables -N openvpn',
            '/sbin/iptables -I INPUT 1 -i tun0 -j openvpn',
            'iptables-save'
        ])

    def test_connect(self):
        from gamoto.management.commands import openvpn
        from gamoto import users

        openvpn.users.sudo = self._fake_sudo
        openvpn.users.getUser = self._fake_get_user

        cmd = openvpn.Command()
        os.environ.setdefault('common_name', 'test')
        os.environ.setdefault('script_type', 'client-connect')
        os.environ.setdefault('ifconfig_pool_remote_ip', '10.88.20.35')

        cmd.handle()

        self.assertListEqual(self.sudo_commands, [
            'iptables-save',
            '/sbin/iptables -N openvpn',
            '/sbin/iptables -I INPUT 1 -i tun0 -j openvpn',
            'iptables-save',
            '/sbin/iptables -A openvpn -i tun0 -s 10.88.20.35 -d 10.1.2.0/24'
            ' -m comment --comment "test"'
        ])

from django.test import TestCase, Client
from django.urls import reverse, exceptions
from django.urls.resolvers import URLPattern
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from bs4 import BeautifulSoup

from gamoto.tests import data

import os
import shutil


# Create your tests here.
class TestRockFace(TestCase):
    def setUp(self):
        from gamoto.management.commands import setup
        cmd = setup.Command()

        cmd._status = lambda var: None
        cmd.stdout.write = lambda var, ending=None: None

        cmd.configureDB()
        self.content_type = ContentType.objects.get(app_label='subnet')

        self.admin = User.objects.create_user(
            username='admin',
            password='12345',
            is_staff=True,
            is_superuser=True
        )
        self.user = User.objects.create_user(
            username='test',
            password='12345'
        )

        self.temp_path = os.path.join(os.getcwd(), '.test_tmp')
        os.makedirs(self.temp_path)
        os.makedirs(os.path.join(self.temp_path, 'users'))
        os.makedirs(os.path.join(self.temp_path, 'ccd'))
        os.makedirs(os.path.join(self.temp_path, 'ca'))

        self.test_settings = {
            'BASE_PATH': self.temp_path,
            'USER_PATH': os.path.join(self.temp_path, 'users'),
            'CA_PATH': os.path.join(self.temp_path, 'ca')
        }

    def tearDown(self):
        shutil.rmtree(self.temp_path)

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
        self.client.login(username='test', password='12345')

    def formTester(self, name, redirects_to, data, kwargs={}):
        self.client.login(username='admin', password='12345')

        url = reverse(name, kwargs=kwargs)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')

        form = soup.form

        self.assertEqual(form['action'], url)

        response = self.client.post(url, data)
        self.assertRedirects(response, reverse(redirects_to))

    def test_create_group(self):
        self.formTester('create_group', 'endpoints', {
            'name': 'test group',
            'default': False,
        })

        group = Group.objects.get(name='test group')

    def test_create_subnet(self):
        group = Group.objects.create(name='test group')
        group.save()

        subnets = ['192.168.0.1', '192.2.3.0/24', '10.10.10.10,10.20.0.0/16',
                   '10.10.0.0/24,10.20.0.0/16']

        for num, subnet in enumerate(subnets):
            self.formTester('add_group_subnet', 'endpoints', {
                'name': 'test subnet %s' % num,
                'subnet': subnet
            }, kwargs={'group_id': group.id})

        db_subnets = group.permissions.all()

        for subnet in db_subnets:
            self.assertIn(subnet.codename.split('_')[-1], subnets)

    def test_add_user_group(self):
        group = Group.objects.create(name='test group')
        group.save()
        perm = Permission.objects.create(
            name='test subnet',
            codename='network_10.1.1.0/24,10.1.2.0/24',
            content_type=self.content_type
        )
        perm.save()
        group.permissions.add(perm)
        group.save()

        with self.settings(**self.test_settings):
            user_groups = self.formTester('user_groups', 'users', {
                'groups': group.id,
            }, kwargs={'user_id': self.user.id})

        from gamoto import openvpn

        routes = openvpn.getRoutes('test')

        self.assertEquals(routes[0], '10.1.1.0/24')
        self.assertEquals(routes[1], '10.1.2.0/24')

    def test_default_group(self):
        with self.settings(**self.test_settings):
            self.formTester('create_group', 'endpoints', {
                'name': 'test group',
                'default': True,
            })

            group = Group.objects.get(name='test group')

            perm = Permission.objects.create(
                name='test subnet',
                codename='network_10.1.1.0/24,10.1.2.0/24',
                content_type=self.content_type
            )
            perm.save()
            group.permissions.add(perm)
            group.save()

            from gamoto import openvpn

            routes = openvpn.getRoutes('test')

            self.assertEquals(routes[0], '10.1.1.0/24')
            self.assertEquals(routes[1], '10.1.2.0/24')


class TestOpenvpn(TestCase):
    def setUp(self):
        self.sudo_commands = []
        self.blank_ipt = False

        self.ipt_copy = [i for i in data.IPTABLES_SAVE]

        from gamoto.management.commands import setup
        cmd = setup.Command()

        cmd._status = lambda var: None
        cmd.stdout.write = lambda var, ending=None: None

        cmd.configureDB()

        self.content_type = ContentType.objects.get(app_label='subnet')

        group = Group.objects.create(name="testgroup")

        perm = Permission.objects.create(
            codename="network_10.1.2.0/24",
            name="My network",
            content_type=self.content_type
        )

        group.permissions.add(perm)
        group.save()

        user = User.objects.create(username="test", email="test@mail.com")
        user.groups.add(group)
        user.save()

    def tearDown(self):
        data.IPTABLES_SAVE = self.ipt_copy

    def _fake_sudo(self, *a):
        for arg in a:
            if ' ' in arg:
                raise Exception(
                    "Space in '%s'. Are arguments split?" % repr(a))
        self.sudo_commands.append(' '.join(a))
        result = b''
        if 'iptables-save' in a:
            if self.blank_ipt:
                result = b'\n'
            else:
                result = bytes('\n'.join(data.IPTABLES_SAVE), encoding='ascii')

        elif a[1] == '-N':
            data.IPTABLES_SAVE.insert(5, ":%s - [0:0]" % a[2])

        elif a[1] == '-t':
            if a[2] == '-A':
                data.IPTABLES_SAVE.insert(6, ' '.join(a[3:]))

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

        tables = cmd.ipt.refreshTables()

        cmd.ipt.setupIptables()

        tables = cmd.ipt.refreshTables()

        self.blank_ipt = False

        self.assertListEqual(self.sudo_commands, [
            'iptables-save', 'iptables-save', 'iptables-save',
            '/sbin/iptables -t filter -N openvpn',
            '/sbin/iptables -t filter -I INPUT 1 -i tun0 -j openvpn',
            '/sbin/iptables -t filter -A INPUT -i tun0 -j DROP',
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
            'iptables-save',
            '/sbin/iptables -t filter -N openvpn',
            '/sbin/iptables -t filter -I INPUT 1 -i tun0 -j openvpn',
            '/sbin/iptables -t filter -A INPUT -i tun0 -j DROP',
            'iptables-save',
            '/sbin/iptables -t filter -A openvpn -i tun0 -s 10.88.20.35 -d'
            ' 10.1.2.0/24 -m comment --comment test -j ACCEPT'
        ])

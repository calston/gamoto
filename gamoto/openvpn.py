# Openvpn helper things
from django.conf import settings
from django.contrib.auth.models import User, Permission, Group

from gamoto import users

import os
import ipaddress


def _readlog(statuslog):
    clients = {}
    with open(statuslog) as log:
        current_stat = None

        for ln in log:
            if ln.startswith('Common Name'):
                current_stat = 'clients'

            elif ln.startswith('Virtual Address'):
                current_stat = 'routes'

            elif ln.startswith('GLOBAL') or ln.startswith('ROUTING'):
                current_stat = None

            elif current_stat == 'clients':
                name, remote_ip, rx, tx, start = ln.strip().split(',')

                clients[name] = {
                    'ip': remote_ip.split(':')[0],
                    'rx_bytes': int(rx),
                    'tx_bytes': int(tx),
                    'connected': start,
                    'virtual': ''
                }

            elif current_stat == 'routes':
                virtual, name, remote, start = ln.strip().split(',')
                clients[name]['virtual'] = virtual
    return clients


def getStatus():
    statuslog = os.path.join(settings.BASE_PATH, 'openvpn-status.log')

    if not os.path.exists(statuslog):
        return {}

    try:
        clients = _readlog(statuslog)
    except PermissionError as err:
        # Try to fix it
        from gamoto import users
        users.sudo(
            'chown',
            '%s:%s' % (settings.GAMOTO_USER, settings.GAMOTO_GROUP),
            statuslog
        )
        clients = _readlog(statuslog)

    return clients


def getClient(name):
    return getStatus().get(name, None)


def getSubnets(group):
    subnets = []
    permissions = group.permissions.filter(content_type__app_label='subnet')
    for p in permissions:
        subnetd = p.codename.split('_')[-1].split(',')

        for subnet in subnetd:
            if subnet not in subnets:
                subnets.append(subnet)

    return subnets

def getRoutes(user):
    if isinstance(user, str):
        user = User.objects.get(username=user)

    pwd = users.getUser(user.username)

    if not (pwd and pwd.get('mfa')):
        return None

    subnets = []
    groups = user.groups.all()

    for group in groups:
        subnets.extend(getSubnets(group))

    default_permission = Permission.objects.get(codename='default_group')

    groups = Group.objects.filter(permissions__codename='default_group')

    for group in groups:
        subnets.extend(getSubnets(group))

    return subnets


def updateCCDs():
    db_users = User.objects.all()

    ccd_path = os.path.join(settings.BASE_PATH, 'ccd')
    if not os.path.exists(ccd_path):
        os.makedirs(ccd_path)

    for user in db_users:
        subnets = getRoutes(user)
        if subnets:
            user_ccd_path = os.path.join(ccd_path, user.username)
            with open(user_ccd_path, 'wt') as user_ccd:
                for subnet in subnets:
                    if not '/' in subnet:
                        subnet += '/32'
                    net = ipaddress.ip_network(subnet)
                    user_ccd.write('push "route %s %s"\n' % (
                        net.network_address.exploded,
                        net.netmask.exploded
                    ))

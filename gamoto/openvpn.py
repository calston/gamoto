# Openvpn helper things
from django.conf import settings

import os


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
                    'connected': start
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

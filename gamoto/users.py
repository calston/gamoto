# Creates and manage users
from django.conf import settings

import subprocess
import pwd


def getUID():
    return pwd.getpwnam(settings.GAMOTO_USER).pw_uid


def createUser(name):
    passwd = None
    try:
        passwd = pwd.getpwnam(name)
    except KeyError:
        pass

    if not passwd:
        subprocess.Popen([
            'sudo', '/usr/sbin/useradd',
            '-b', '/var/lib/gamoto',
            '-s', '/bin/false',
            '-N', name
        ])
        subprocess.Popen([
            'sudo', 'mkdir', '/var/lib/gamoto/%s' % name
        ])
        subprocess.Popen([
            'sudo', 'chown', '%s:nogroup', '/var/lib/gamoto/%s' % name
        ])
    print(passwd)

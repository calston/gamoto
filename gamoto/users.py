# Creates and manage users
from django.conf import settings

import subprocess
import pwd
import os


def getSystemUID():
    return pwd.getpwnam(settings.GAMOTO_USER).pw_uid


def getUser(name):
    """
    Check if a user exists and return all the info about them
    as a dict
    """
    try:
        passwd = pwd.getpwnam(name)

        return {
            'name': passwd.pw_name,
            'uid': passwd.pw_uid,
            'gid': passwd.pw_gid,
            'gecos': passwd.pw_gecos,
            'home': passwd.pw_dir,
            'shell': passwd.pw_shell
        }
    except KeyError:
        return None


def createUser(name):
    passwd = getUser(name)

    if not passwd:
        subprocess.Popen([
            'sudo', '/usr/sbin/useradd',
            '-s', '/bin/false',
            '-b', settings.USER_PATH,
            '-g', settings.GAMOTO_GROUP,
            '-N', '-M', name
        ]).wait()
        subprocess.Popen([
            'sudo', 'mkdir', os.path.join(settings.USER_PATH, name)
        ]).wait()
        subprocess.Popen([
            'sudo',
            'chown',
            '%s:%s' % (name, settings.GAMOTO_GROUP),
            os.path.join(settings.USER_PATH, name)
        ]).wait()

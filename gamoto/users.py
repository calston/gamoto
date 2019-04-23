# Creates and manage users
from django.conf import settings

import pyotp

import subprocess
import random
import pwd
import os


def getSystemUID():
    return pwd.getpwnam(settings.GAMOTO_USER).pw_uid


def sudo(*a):
    proc = subprocess.Popen(['sudo'] + list(a), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    return proc.communicate()


def getUser(name):
    """
    Check if a user exists and return all the info about them
    as a dict
    """
    try:
        passwd = pwd.getpwnam(name)
    except KeyError:
        return None

    stdout, stderr = sudo(
        'stat', os.path.join(passwd.pw_dir, '.google_authenticator')
    )

    if stdout:
        mfa = True
    else:
        mfa = False

    return {
        'name': passwd.pw_name,
        'uid': passwd.pw_uid,
        'gid': passwd.pw_gid,
        'gecos': passwd.pw_gecos,
        'home': passwd.pw_dir,
        'shell': passwd.pw_shell,
        'mfa': mfa
    }


def createUser(name):
    passwd = getUser(name)

    if not passwd:
        sudo(
            '/usr/sbin/useradd',
            '-s', '/bin/false',
            '-b', settings.USER_PATH,
            '-g', settings.GAMOTO_GROUP,
            '-N', '-M', name
        )
        sudo('mkdir', os.path.join(settings.USER_PATH, name))
        sudo(
            'chown',
            '%s:%s' % (name, settings.GAMOTO_GROUP),
            os.path.join(settings.USER_PATH, name)
        )


def configureTOTP(name):
    key = pyotp.random_base32()

    totp = pyotp.totp.TOTP(key)

    google_auth = os.path.join(settings.USER_PATH, name,
                               '.google_authenticator')

    proc = subprocess.Popen(
        ['sudo', 'tee', google_auth],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    codes = [str(random.randint(10000000, 99999999)) for i in range(5)]

    authfi = '\n'.join([key, '" RATE_LIMIT 3 30', '" TOTP_AUTH'] + codes)

    r = proc.communicate(bytes(authfi+'\n', encoding='ascii'))

    sudo('chown', '%s:%s' % (name, settings.GAMOTO_GROUP), google_auth)
    sudo('chmod', '0600', google_auth)

    return (
        codes,
        totp.provisioning_uri(name, issuer_name=settings.GAMOTO_ISSUER_NAME)
    )

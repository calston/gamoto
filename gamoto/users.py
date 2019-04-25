# Creates and manage users
from django.conf import settings

from gamoto import ca

from io import BytesIO

import pyotp

import subprocess
import random
import pwd
import os
import shutil
import zipfile


def getSystemUID():
    return pwd.getpwnam(settings.GAMOTO_USER).pw_uid


def sudo(*a):
    proc = subprocess.Popen(['sudo'] + list(a), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    return proc.communicate()


def sudoWrite(filename, data):
    proc = subprocess.Popen(
        ['sudo', 'tee', filename],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    r = proc.communicate(bytes(data, encoding='ascii'))


def sudoRead(filename):
    proc = subprocess.Popen(
        ['sudo', 'cat', filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    data, err = proc.communicate()

    if err:
        raise Exception(err)

    return data


def createVPN(name):
    myca = ca.CertificateAuthority(
        settings.CA_SETUP['ou'],
        settings.CA_SETUP['org'],
        settings.CA_SETUP['email'],
        settings.CA_SETUP['country'],
        settings.CA_SETUP['state'],
        settings.CA_SETUP['city'],
        key_path=settings.CA_PATH
    )

    myca.createCSR(name)
    myca.signCSR(name)


def getVPNZIP(name):
    user_cert = os.path.join(settings.CA_PATH, name + '.crt')
    user_key = os.path.join(settings.CA_PATH, name + '.key')
    server_cert = os.path.join(settings.CA_PATH, 'ca.crt')

    if not os.path.exists(user_cert):
        raise Exception("Certificate does not exist")

    config = [
        "client",
        "dev tun",
        "proto udp",
        "remote %s %s" % (settings.OPENVPN_HOSTNAME, settings.OPENVPN_PORT),
        "resolv-retry infinite",
        "nobind",
        "persist-key",
        "persist-tun",
        "ca ca.crt",
        "cert %s.crt" % name,
        "key %s.key" % name,
        "verb 3",
        "auth-user-pass"
    ]

    zip_io = BytesIO()

    with zipfile.ZipFile(zip_io, mode="w") as vpnzip:
        vpnzip.write(str(user_cert), arcname=name + '.crt')
        vpnzip.write(str(user_key), arcname=name + '.key')
        vpnzip.write(str(server_cert), arcname='ca.crt')

        vpnzip.writestr('client.ovpn', '\n'.join(config))

    return zip_io.getvalue()


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
    google_auth = os.path.join(settings.USER_PATH, name,
                               '.google_authenticator')
    key = pyotp.random_base32()
    totp = pyotp.totp.TOTP(key)

    codes = [str(random.randint(10000000, 99999999)) for i in range(5)]
    authfi = '\n'.join([key, '" RATE_LIMIT 3 30', '" TOTP_AUTH'] + codes)

    sudoWrite(google_auth, authfi + '\n')

    sudo('chown', '%s:%s' % (name, settings.GAMOTO_GROUP), google_auth)
    sudo('chmod', '0600', google_auth)

    uri = totp.provisioning_uri(name, issuer_name=settings.CA_SETUP['org'])
    return (codes, uri)

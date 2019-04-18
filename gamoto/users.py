# Creates and manage users
import subprocess
import pwd


def createUser(name):
    passwd = None
    try:
        passwd = pwd.getpwnam(name)
    except KeyError:
        pass

    if not passwd:
        proc = subprocess.Popen([
            'sudo', '/usr/sbin/useradd',
            '-b', '/var/lib/gamoto',
            '-s', '/bin/false',
            '-N', name
        ])
        proc = subprocess.Popen([
            'sudo', 'mkdir', '/var/lib/gamoto/%s' % name
        ])
        proc = subprocess.Popen([
            'sudo', 'chown', '%s:nogroup', '/var/lib/gamoto/%s' % name
        ])
    print(passwd)

if __name__ == "__main__":
    createUser('colin.alston')

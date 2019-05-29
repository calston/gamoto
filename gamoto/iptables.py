from django.conf import settings

from gamoto import users


class IPTables(object):
    def __init__(self):
        self.tables = {
            'filter': {
                'INPUT': {'rules': [], 'default': None},
                'OUTPUT': {'rules': [], 'default': None},
                'FORWARD': {'rules': [], 'default': None}
            },
            'nat': {
                'PREROUTING': {'rules': [], 'default': None},
                'INPUT': {'rules': [], 'default': None},
                'OUTPUT': {'rules': [], 'default': None},
                'POSTROUTING': {'rules': [], 'default': None}
            }
        }

        self.refreshTables()

    def refreshTables(self):
        result, err = users.sudo('iptables-save')
        result = result.strip()

        if err:
            raise Exception(err)

        rules = [i for i in result.decode().split('\n')
                 if not i.startswith('#')]

        for r in rules:
            if r.startswith('*'):
                table = r.strip('*')
                if table not in self.tables:
                    self.tables[table] = {}
            elif r.startswith(':'):
                chain, default, b = r.strip(':').split()
                if default == '-':
                    default = None

                self.tables[table][chain] = {
                    'default': default,
                    'rules': []
                }
            elif r.startswith('-'):
                token, chain, args = r.split(None, 2)
                self.tables[table][chain]['rules'].append(args)

    def iptables(self, *rule):
        result, err = users.sudo('/sbin/iptables', *rule)
        if err:
            raise Exception(err)

    def getTable(self, table):
        return self.tables.get(table, {})

    def getChain(self, table, chain):
        return self.tables.get(table, {}).get(chain, {})

    def createChain(self, table, chain):
        if chain not in self.getTable(table):
            self.iptables('-t', table, '-N', chain)

    def addRule(self, table, chain, match, action, comment=None, top=False):
        rules = self.getChain(table, chain).get('rules', [])

        rtest = [match, '-j', action]
        if comment:
            rtest.append('-m comment --comment %s' % comment)

        if ' '.join(rtest) in rules:
            return

        rule = ['-t', table]

        if top:
            rule.extend(['-I', chain, '1'])
        else:
            rule.extend(['-A', chain])

        rule.extend(match.split())

        if comment:
            rule.extend(['-m', 'comment', '--comment', comment])

        rule.extend(['-j', action])

        self.iptables(*rule)

    def setupIptables(self):
        # Makes sure iptables has our chain
        self.refreshTables()

        self.createChain('filter', 'openvpn')

        input_rules = self.getChain('filter', 'INPUT').get('rules', [])

        self.addRule('filter', 'INPUT', '-i ' + settings.VPN_INTERFACE,
                     'openvpn', top=True)

        if settings.DEFAULT_DENY:
            self.addRule('filter', 'INPUT', '-i ' + settings.VPN_INTERFACE,
                         'DROP')

    def allowClient(self, name, src, dest):
        self.refreshTables()
        if not (name and src and dest):
            return None

        rule = '-i %s -s %s -d %s' % (settings.VPN_INTERFACE, src, dest)

        self.addRule('filter', 'openvpn', rule, 'ACCEPT', comment=name)

    def flushClient(self, name):
        self.refreshTables()
        rules = self.getChain('filter', 'openvpn').get('rules', [])

        for i, r in reversed(list(enumerate(rules))):
            if name in r:
                self.iptables('-t', 'filter', '-D', 'openvpn', '%s' % (i+1))

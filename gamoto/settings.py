"""
Django settings for gamoto project.
"""
import configparser
import os


GAMOTO_USER = 'gamoto'
GAMOTO_GROUP = 'gamoto'

BASE_PATH = '/var/lib/gamoto'
CA_PATH = os.path.join(BASE_PATH, 'ca')
USER_PATH = os.path.join(BASE_PATH, 'users')

OPENVPN_PORT = 1194
OPENVPN_HOSTNAME = 'vpn.acme.zp'

PAGE_TITLE = 'Gamoto'

VPN_INTERFACE = 'tun0'

MANAGE_IPTABLES = True

CA_SETUP = {
    'org': 'ACME Corp',
    'ou': 'IT',
    'email': 'support@acme.zp',
    'city': 'ACME Village',
    'state': 'Assur',
    'country': 'US'
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '%#*6c91zihs)_ptl1t3sxu$$#a)bah)wv8$-i6m*646x_gsl+n'

DEBUG = False

ALLOWED_HOSTS = ['*']

LOGOUT_REDIRECT_URL = "/"
LOGIN_REDIRECT_URL = "/"

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

GOOGLE_AUTH = False
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'gamoto'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gamoto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "gamoto/templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gamoto.wsgi.application'


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_PATH, "static")

# Read system config

config = configparser.ConfigParser()
config.read('/etc/gamoto/gamoto.conf')
# Witchcraft
if 'main' in config:
    # Get MFA setting
    MFA_ENABLED = config['main'].getboolean('2fa', True)

    GAMOTO_USER = config['main'].get('user', GAMOTO_USER)
    GAMOTO_GROUP = config['main'].get('group', GAMOTO_GROUP)

    # Default paths
    BASE_PATH = config['main'].get('path', BASE_PATH)
    CA_PATH = config['main'].get('ca_path', os.path.join(BASE_PATH, 'ca'))
    USER_PATH = config['main'].get('home_path',
                                   os.path.join(BASE_PATH, 'users'))

    STATIC_PATH = config['main'].get(
        'static_path', os.path.join(BASE_PATH, 'static'))

    SECRET_KEY = config['main'].get('cookie_secret', SECRET_KEY)
    MANAGE_IPTABLES = config['main'].getboolean('manage_iptables',
                                                MANAGE_IPTABLES)

    PAGE_TITLE = config['main'].get('page_title', PAGE_TITLE)

    DEBUG = config['main'].getboolean('debug', DEBUG)

if 'google' in config:
    GOOGLE_AUTH = True
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config['google'].get('key', None)
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config['google'].get('secret', None)
    whitelisted = config['google'].get('allowed_domains', None)
    if whitelisted:
        whitelisted = whitelisted.replace(' ', '').split(',')
        SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS = whitelisted

if 'openvpn' in config:
    # Openvpn settings
    OPENVPN_PORT = config['openvpn'].get('port', OPENVPN_PORT)
    OPENVPN_HOSTNAME = config['openvpn'].get('hostname', OPENVPN_HOSTNAME)

if 'ca' in config:
    # Merge CA config
    for key in CA_SETUP.keys():
        CA_SETUP[key] = config['ca'].get(key, CA_SETUP[key])

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_PATH, 'gamoto.db'),
    }
}

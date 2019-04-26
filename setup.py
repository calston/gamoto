from setuptools import setup, find_packages

setup(
    name='gamoto',
    version='0.0.3',
    url='http://github.com/calston/gamoto',
    description='A web portal for VPN self service',
    classifiers=[
        "Programming Language :: Python",
    ],
    author='Colin Alston',
    author_email='colin.alston@gmail.com',
    license='BSD',
    packages=find_packages(),
    scripts=['bin/gamoto'],
    include_package_data=True,
    install_requires=[
        'pyopenssl',
        'django==2.2',
        'social-auth-app-django',
        'pyotp',
        'gunicorn'
    ],
)

from setuptools import setup, find_packages

setup(
    name='gamoto',
    version='0.0.1',
    description='Gamoto',
    classifiers=[
        "Programming Language :: Python",
    ],
    author='Colin Alston',
    author_email='colin.alston@gmail.com',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pyopenssl',
        'django==2.2',
        'social-auth-app-django'
    ],
)

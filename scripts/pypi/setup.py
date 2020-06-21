import os
from setuptools import find_packages, setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='slothy',
    version='0.0.2',
    packages=find_packages(),
    install_requires=['Django', 'django_rest_framework', 'six', 'django-cors-headers'],
    include_package_data=True,
    license='BSD License',
    description='Slothy framework',
    long_description='',
    url='https://github.com/brenokcc/slothy',
    author='Carlos Breno Pereira Silva',
    author_email='brenokcc@yahoo.com.br',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)

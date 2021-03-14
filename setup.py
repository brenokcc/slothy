import os
from subprocess import check_call
from setuptools import find_packages, setup
from setuptools.command.install import install


os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


class PostInstallCommand(install):

    def run(self):
        check_call("echo :)".split())
        install.run(self)


setup(
    name='slothy',
    version='0.0.1',
    packages=find_packages(),
    install_requires=['six', 'django', 'django-cors-headers', 'Pillow', 'wheel', 'gunicorn'],
    extras_require={
        'frontend': []
    },
    scripts=[],
    include_package_data=True,
    license='BSD License',
    description='Metadata-based web framework for the development of management information systems',
    long_description='',  # README,
    cmdclass={
        'install': PostInstallCommand,
    },
    url='http://slothy.aplicativo.click/',
    author='Breno Silva',
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

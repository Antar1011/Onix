import versioneer
from setuptools import setup
from onix import __author__

setup(
    name='Onix',
    description='The Pokemon data mining package',
    packages=['onix'],
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    url='https://github.com/Antar1011/Onix',
    license='GPL v3',
    author=__author__,
    author_email='antar@smgoon.com',
    install_requires=[
        "future",
        "pygithub",
        "py-mini-racer>=0.1.6",
        "setuptools>=0.8",
        "sqlalchemy>=1.0.0"
    ],
    include_package_data=True
)


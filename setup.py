from setuptools import setup, find_packages
from os import path
import time

if path.exists("VERSION.txt"):
    # this file can be written by CI tools
    with open("VERSION.txt") as version_file:
        version = version_file.read().strip().strip("v")
else:
    version = str(time.time())

setup(
    name='ckangpt',
    version=version,
    packages=find_packages(exclude=['contrib', 'docs', 'tests*', 'poc']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'ckangpt = ckangpt.cli:main',
        ]
    },
)

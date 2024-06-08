from setuptools import setup, find_packages
from os import path
import time

if path.exists('VERSION'):
    # this file can be written by CI tools
    with open('VERSION') as version_file:
        version = version_file.read().strip().strip("v")
else:
    version = str(time.time())

setup(
    name='odds',
    version=version,
    packages=find_packages(exclude=['contrib', 'docs', 'tests*', 'poc', 'utils']),
    include_package_data=True,
)

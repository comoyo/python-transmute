import os
from setuptools import find_packages, setup

version = 0
if 'HELLO_VERSION' in os.environ:
    version = os.environ['HELLO_VERSION'] 

setup(name='hello', version=version, packages=['hello'],
        description='A module to say \'Hi!\'', zip_safe=True)

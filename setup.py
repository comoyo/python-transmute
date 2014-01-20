# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

execfile('transmute/version.py') # defines __version__

project_metadata = {
    'name':         'transmute',
    'version':      __version__,
    'author':       'João Abecasis',
    'author_email': 'joao@comoyo.com',
    'url':          'https://github.com/comoyo/python-transmute',
    'description':  'Automatically update Python Eggs on application startup.',
    'classifiers':  [
                        "Programming Language :: Python",
                        "License :: OSI Approved :: Apache Software License",
                        "Operating System :: OS Independent",
                        "Development Status :: 3 - Alpha",
                        "Intended Audience :: Developers",
                        "Topic :: Software Development :: Libraries :: Python Modules",
                        "Topic :: System :: Installation/Setup",
                        "Topic :: System :: Software Distribution",
                    ],
    'packages':     find_packages(exclude=[ 'tests*' ]),
}
setup(**project_metadata)

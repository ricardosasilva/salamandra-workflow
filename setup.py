#!/usr/bin/env python
from setuptools import setup, find_packages


requirements = [
    'workalendar==10.3.0',
    'humanize==2.6.0'
]

setup(
    name='salamandra-workflow',
    version='1.2.0',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest',
            'pytest-pep8',
            'pytest-cov',
            'mimesis-factory',
            'factory-boy'
        ]
    }
)

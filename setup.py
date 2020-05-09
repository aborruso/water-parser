#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

setup(
    name='water-parser',
    version='0.1.0',
    url='https://github.com/glefait/water-parser',
    author="Guillem Lefait",
    author_email='guillem@datamq.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    description="water-parser",
    long_description=readme,
    include_package_data=True,
    packages=['{}'.format(x) for x in find_packages('src')],
    package_dir={'': 'src'},
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'water_parser=water_parser.cli:main',
        ],
    },
    install_requires=[
        'click~=7.0',
        'beautifulsoup4'
    ],
)

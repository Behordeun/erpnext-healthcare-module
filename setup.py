# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in lafia/__init__.py
from lafia import __version__ as version

setup(
	name='lafia',
	version=version,
	description='Integrations for lafia.io app',
	author='ParallelScore',
	author_email='m.emereuwa@parallelscore.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)

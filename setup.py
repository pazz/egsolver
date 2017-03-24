#!/usr/bin/env python3
# Copyright (C) 2017  Patrick Totzke <patricktotzke@gmail.com>
# This file is released under the GNU GPL, version 3 or a later revision.

from setuptools import setup, find_packages
import egsolver


setup(name='egsolver',
      version=egsolver.__version__,
      description=egsolver.__description__,
      author=egsolver.__author__,
      author_email=egsolver.__author_email__,
      url=egsolver.__url__,
      license=egsolver.__copyright__,
      packages=find_packages(),
      entry_points={
          'console_scripts':
              ['egsolver = egsolver.main:main'],
      },
      install_requires=['networkx'],
      provides=['egsolver'],
      )

#!/usr/bin/env python

from __future__ import print_function
import glob
import os
import sys
from setuptools import setup, find_packages
from shutil import copyfile, copytree, rmtree

if sys.version_info < (2, 7):
    print("Python versions prior to 2.7 are not supported for pip installed PyMLSQL.",
          file=sys.stderr)
    sys.exit(-1)

try:
    exec(open('pymlsql/version.py').read())
except IOError:
    print("Failed to load PyMLSQL version file for packaging.",
          file=sys.stderr)
    sys.exit(-1)

VERSION = __version__

_minimum_pandas_version = "0.19.2"
_minimum_pyarrow_version = "0.8.0"

setup(
    name='pymlsql',
    version=VERSION,
    description='MLSQL Python API',
    long_description="With this lib you can develop Python ML project in MLSQL",
    author='ZhuWilliam',
    author_email='allwefantasy@gmail.com',
    url='https://github.com/allwefantasy/PyMLSQL',
    packages=['pymlsql',
              'pymlsql.utils',
              'pymlsql.api',
              'pymlsql.aliyun',
              'pymlsql.aliyun.dev'
              ],
    include_package_data=True,
    license='http://www.apache.org/licenses/LICENSE-2.0',
    install_requires=[
        'click>=6.7',
        'py4j==0.10.8.1',
        'numpy>=1.7',
        'aliyun-python-sdk-ecs',
        'pyarrow>=%s' % _minimum_pyarrow_version,
        'pandas>=%s' % _minimum_pandas_version],
    entry_points='''
        [console_scripts]
        pymlsql=pymlsql.cli:cli
    ''',
    setup_requires=['pypandoc'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy']
)

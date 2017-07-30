#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
from setuptools import setup, find_packages


setup(
    name='async-spider',
    version='0.0.1',
    description='ASynchronous Spidering Essential Tool (ASSET). ',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Security',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS'
    ],
    keywords='asset security spidering crawler async graph report',
    url='https://github.com/panagiks/ASSET',
    author='panagiks',
    license='MIT',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    namespace_packages=['async_spider'],
    extras_require={
        'graph': [
            'pygraphviz',
            'networkx'
        ]
    },
    install_requires=[
        'aiohttp',
        'bs4'
    ],
    entry_points={
        'console_scripts': [
            'async-spider=async_spider.spider:main'
        ]
    }
)

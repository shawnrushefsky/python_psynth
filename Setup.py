__author__ = 'psymac0'
import os
from setuptools import setup

setup(
    name="psynth",
    version="0.1.0rcN",
    description="An open-source Python library for generating graphs in Psymphonic Psynth.",
    url="http://shawnrushefsky.github.io/python_psynth",
    license='MIT',
    install_requires=['requests', 'simplejson'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approves :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database :: Front-Ends',
        'Topic :: Education',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'Topic :: Office/Business :: Financial :: Spreadsheet',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development :: Libraries'
    ],
    keywords='psynth psymphonic graph graphdb visualize network'
)
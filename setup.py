#!/usr/bin/env python
import glob
import os
from codecs import open

from setuptools import find_packages, setup

data_files = []
directories = glob.glob('async_tls_client/dependencies/')
for directory in directories:
    files = glob.glob(directory + '*')
    data_files.append(('async_tls_client/dependencies', files))

about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "async_tls_client", "__version__.py"), "r", "utf-8") as f:
    exec(f.read(), about)

with open("README.md", "r", "utf-8") as f:
    readme = f.read()

setup(
    name=about["__title__"],
    version=about["__version__"],
    author=about["__author__"],
    description=about["__description__"],
    license=about["__license__"],
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/diprog/python-tls-client-async",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['*'],
    },
    python_requires=">=3.9",
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries",
    ],
    install_requires=["typing-extensions"],
    project_urls={
        "Original Project": "https://github.com/FlorianREGAZ/Python-Tls-Client",
        "Original PyPI": "https://pypi.org/project/tls-client/",
        "Source": "https://github.com/diprog/python-tls-client-async",
    },
    keywords=["tls", "asyncio", "http-client", "ja3", "fingerprinting"],
)

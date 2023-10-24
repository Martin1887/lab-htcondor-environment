#! /usr/bin/env python

from setuptools import find_packages, setup


with open("README.md") as f1:
    long_description = f1.read()


setup(
    name="lab-htcondor-environment",
    version="1.0.1",
    description="HTCondor environment for Lab and Downward Lab",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    keywords="benchmarks cluster grid",
    author="Martín Pozo",
    author_email="mpozo@protonmail.com",
    url="https://github.com/Martin1887/lab-htcondor-environment",
    license="GPL3+",
    packages=find_packages("."),
    package_data={"lab_htcondor_environment": ["data/*"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
    ],
    install_requires=["lab"],
    python_requires=">=3.7",
)

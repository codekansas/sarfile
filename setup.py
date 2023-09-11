#!/usr/bin/env python
"""Setup script for the sarfile module."""

import re

from setuptools import setup

REQUIREMENTS = []

REQUIREMENTS_DEV = [
    "black",
    "darglint",
    "mypy",
    "pytest",
    "pytest-timeout",
    "ruff",
]


with open("README.md", "r", encoding="utf-8") as f:
    long_description: str = f.read()


# Parses the version from `sarfile/__init__.py`.
with open("sarfile/__init__.py", "r", encoding="utf-8") as fh:
    version_re = re.search(r"^__version__ = \"([^\"]*)\"", fh.read(), re.MULTILINE)
assert version_re is not None, "Could not find version in ml/__init__.py"
version: str = version_re.group(1)


setup(
    name="sarfile",
    version=version,
    description="ML project template repository",
    author="Benjamin Bolte",
    url="https://github.com/codekansas/sarfile",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.10",
    install_requires=REQUIREMENTS,
    tests_require=REQUIREMENTS_DEV,
    extras_require={"dev": REQUIREMENTS_DEV},
    package_data={"ml": ["py.typed", "requirements.txt"]},
)

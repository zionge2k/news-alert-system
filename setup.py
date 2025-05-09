"""
Setup script for development mode installation.
"""

from setuptools import find_packages, setup

setup(
    name="news-alert-system",
    version="0.1.0",
    packages=find_packages(
        include=[
            "app",
            "common",
            "pipelines",
            "infra",
            "infra.*",
            "utils",
            "utils.*",
        ]
    ),
    python_requires=">=3.11",
)

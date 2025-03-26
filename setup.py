# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="dataagents",
    version="0.1.0",
    author="Alex Hou",
    author_email="houalex@gmail.com",
    description="智能数据治理工具集",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(include=["core", "core.*", "dataagents", "dataagents.*"]),
    install_requires=[
        "autogen>=0.2.0",
        "minio>=7.0.0",
        "pandas>=1.3.0",
        "scikit-learn>=1.0.0",
        "plotly>=5.0.0",
        "great-expectations>=0.15.0",
        "pydantic>=1.10.0",
        "requests>=2.26.0"
    ],
    python_requires=">=3.8"
)

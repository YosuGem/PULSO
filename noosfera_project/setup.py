#!/usr/bin/env python
"""Noósfera installer."""

from setuptools import setup
import tomllib

with open("pyproject.toml", "rb") as f:
    datos = tomllib.load(f)

setup(**datos["project"])

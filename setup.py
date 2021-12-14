import re

from setuptools import setup

version = ""
with open("quart_discord/__init__.py") as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

requirements = []
with open("requirements.txt") as f:
    requirements = f.read().splitlines()


setup(
    name="quart_discord",
    author="AlexFlipnote",
    url="https://github.com/xelA/quart_discord",
    version=version,
    packages=["quart_discord"],
    description="Simple project that makes handling Discord OAuth2 easier eith quart",
    include_package_data=True,
    install_requires=requirements
)

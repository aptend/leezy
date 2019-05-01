from setuptools import setup

with open("readme.md", 'r', encoding='utf8') as f:
    long_description = f.read()

setup(
    name='leeyzer',
    version='0.1.0',
    description='leezyer: leetcode lazyer',
    license="MIT",
    long_description=long_description,
    author='aptend',
    packages=['leeyzer'],  # same as name
)

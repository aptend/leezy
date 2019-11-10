from setuptools import setup

with open("readme.md", 'r', encoding='utf8') as f:
    long_description = f.read()

setup(
    name='leezy',
    version='0.1.0',
    description='leezy: leetcode lazyer',
    license="MIT",
    long_description=long_description,
    author='aptend',
    url='aptend@hotmail.com',
    packages=['leezy']
)

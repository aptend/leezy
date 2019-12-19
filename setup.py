from setuptools import setup

with open("readme.md", 'r', encoding='utf8') as f:
    long_description = f.read()

setup(
    name='leezy',
    version='0.2.0',
    description='leezy: leetcode helper for the lazy',
    license="MIT",
    long_description=long_description,
    author='aptend',
    url='aptend@hotmail.com',
    packages=['leezy'],
    install_requires=['requests', 'pytest']
)

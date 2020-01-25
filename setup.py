from setuptools import setup

with open("README.md", 'r', encoding='utf8') as f:
    long_description = f.read()

setup(
    name='leezy',
    version='0.3.3',
    description='leezy: leetcode helper for the lazy',
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='aptend',
    author_email='aptend@hotmail.com',
    url='https://github.com/aptend/leezy',
    entry_points={
        'console_scripts': [
            'leezy = leezy.__main__:dummy_main'
        ]
    },
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Text Processing',
        'Topic :: Utilities'
    ],
    packages=['leezy'],
    install_requires=['requests>=2.18.0', 'pytest>=5.1.3'],
    python_requires='>=3.6'
)

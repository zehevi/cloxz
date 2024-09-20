from setuptools import setup, find_packages

setup(
    name='clock-cli',
    version='0.2',
    packages=find_packages(),
    install_requires=[
        'click',
        'pynput'
    ],
    entry_points={
        'console_scripts': [
            'clock=clock.main:main',
        ],
    },
)

from setuptools import setup, find_packages

setup(
    name='clockz-cli',
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
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown'
)

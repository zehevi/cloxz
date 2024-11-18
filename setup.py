from setuptools import setup, find_packages

setup(
    name='cloxz-cli',
    version='0.4.0',
    packages=find_packages(),
    install_requires=[
        'typer',
        'rich'
    ],
    entry_points={
        'console_scripts': [
            'cxz=clock.main:main',
        ],
    },
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown'
)

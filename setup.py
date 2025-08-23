from setuptools import setup, find_packages

setup(
    name="cloxz",
    version="0.6.2",
    packages=find_packages(),
    install_requires=["typer", "rich"],
    entry_points={
        "console_scripts": [
            "cxz=clock.main:app",
        ],
    },
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)

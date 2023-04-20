"""Setup.py"""
from setuptools import setup


def read_file(name):
    """Read file contents

    Args:
        name (str): name of file

    Returns:
        str: file contents
    """
    with open(name, encoding="utf-8") as file:
        return file.read().encode()


setup(
    name="operations-engineering-reports",
    version="0.1.0",
    author="Operations-Engineering team",
    author_email="operations-engineering@digital.justice.gov.uk",
    packages=["report_app"],
    url="http://pypi.python.org/pypi/operations-engineering-reports/",
    license=read_file("LICENSE"),
    description="Web application to receive JSON data via authenticated POSTs, & serve reports as HTML/JSON",
    long_description=read_file("README.md"),
    install_requires=[
        "flask",
    ],
)

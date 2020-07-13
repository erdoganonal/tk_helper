import setuptools

from tkhelper.package_info import __version__

with open("README.md", "r") as file:
    long_description = file.read()

setuptools.setup(
    name="tkhelper",
    version=__version__,
    author="Erdogan Onal",
    author_email="erdoganonal@windowslive.com",
    description="A module to display some customized tkinter modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/erdoganonal/tk_helper",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.3',
)

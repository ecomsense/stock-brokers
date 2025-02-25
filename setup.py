from setuptools import setup, find_packages

setup(
    name="stock-brokers",
    version="0.0.2",
    description="A general stock broker package",
    author="darkseid",
    author_email="uberdeveloper001@gmail.com",
    packages=find_packages(include=["fake", "finvasia"]),  # Explicit package list
    py_modules=["base"],  # Manually include base.py
    python_requires=">=3.9",
)

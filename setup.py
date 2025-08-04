from setuptools import setup, find_packages

setup(
    name="trip-mvp",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'click',
        'boto3',
        'python-dotenv'
    ],
)
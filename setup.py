# Package repo for distribution
from setuptools import setup, find_packages

setup(
    name="met",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "python-dotenv"
    ],
    entry_points={
        "console_scripts": [
            "fetch-met-office=src.fetch_met_office:main",
            "fetch-asdi=src.fetch_asdi:main"
        ]
    },
    author="Alexander Hall",
    author_email="alexander.hall@rainyrefunds.com",
    description="A tool to fetch weather data from the MET Office API and ASDI archives.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rainyrefundsltd/met",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)

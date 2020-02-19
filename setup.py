import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="derpi_get",
    version="0.3",
    author="LMquentinLR",
    description="A simple implementation of a derpibooru metadata and image scraper.",
    long_description=long_description,
    long_description_content_type="text/markdown",
	url = "https://github.com/LMquentinLR/derpi_get",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="minizinc",
    version="0.0.1",
    author="Jip J. Dekker",
    author_email="jip.dekker@monash.edu",
    description="Access MiniZinc directly from Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://minizinc.org",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
    ],
)

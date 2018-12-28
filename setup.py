import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="minizinc",
    version="0.0.1",
    python_requires='>=3',
    author="Jip J. Dekker",
    author_email="jip.dekker@monash.edu",
    description="Access MiniZinc directly from Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://minizinc.org",
    project_urls={
        'Bug Tracker': 'https://gitlab.com/minizinc/python/issues',
        'Documentation': 'http://minizinc.org/doc-latest',
        'Source': 'https://gitlab.com/minizinc/python',
    },
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
)

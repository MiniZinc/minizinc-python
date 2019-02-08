from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="minizinc",
    version="0.1.0-alpha.2",
    python_requires='>=3.6',
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
    packages=find_packages(where="src"),
    package_dir={'': 'src'},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
)

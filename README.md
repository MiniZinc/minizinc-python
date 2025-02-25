<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/MiniZinc/minizinc-python">
    <img src="https://www.minizinc.org/MiniZn_logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">MiniZinc Python</h3>

  <p align="center">
    The python package that allows you to access all of MiniZinc's functionalities directly from Python.
    <br />
    <a href="https://python.minizinc.dev/en/latest/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/MiniZinc/minizinc-python/issues">Report Bug</a>
    ·
    <a href="https://github.com/MiniZinc/minizinc-python/issues">Request Feature</a>
  </p>
</p>


<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
* [Getting Started](#getting-started)
  * [Installation](#installation)
  * [Usage](#usage)
* [Testing](#testing)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)
<!-- * [Acknowledgements](#acknowledgements) -->


<!-- ABOUT THE PROJECT -->
## About The Project

_MiniZinc Python_ provides an interface from Python to the MiniZinc driver. The
most important goal of this project are to allow easy access to MiniZinc using
native Python structures. This will allow you to more easily make scripts to run
MiniZinc, but will also allow the integration of MiniZinc models within bigger
(Python) projects. This module also aims to expose an interface for meta-search.
For problems that are hard to solve, meta-search can provide solutions to reach
more or better solutions quickly.


<!-- GETTING STARTED -->
## Getting Started

To get a MiniZinc Python up and running follow these simple steps.

### Installation

_MiniZinc Python_ can be installed by running `pip install minizinc`. It
requires [MiniZinc](https://www.minizinc.org/) 2.6+ and
[Python](https://www.python.org/) 3.8+ to be installed on the system. MiniZinc
python expects the `minizinc` executable to be available on the executable path,
the `$PATH` environmental variable, or in a default installation location.

_For more information, please refer to the
[Documentation](https://python.minizinc.dev/en/latest/)_


### Usage

Once all prerequisites and MiniZinc Python are installed, a `minizinc` module
will be available in Python. The following Python code shows how to run a
typical MiniZinc model.

```python
import minizinc

# Create a MiniZinc model
model = minizinc.Model()
model.add_string("""
var -100..100: x;
int: a; int: b; int: c;
constraint a*(x*x) + b*x = c;
solve satisfy;
""")

# Transform Model into a instance
gecode = minizinc.Solver.lookup("gecode")
inst = minizinc.Instance(gecode, model)
inst["a"] = 1
inst["b"] = 4
inst["c"] = 0

# Solve the instance
result = inst.solve(all_solutions=True)
for i in range(len(result)):
    print("x = {}".format(result[i, "x"]))
```

_For more examples, please refer to the
[Documentation](https://python.minizinc.dev/en/latest/)_

<!-- TESTING INSTRUCTIONS -->
## Testing

MiniZinc Python uses [uv](https://docs.astral.sh/uv/) to manage its
dependencies. To install the development dependencies run `uv sync --dev`.

Although continuous integration will test any code, it can be convenient to run
the tests locally. The following commands can be used to test the MiniZinc
Python package.

- We use [PyTest](https://docs.pytest.org/en/stable/) to run a suite of unit
tests. You can run these tests by executing:
```bash
uv run pytest
```
- We use [Ruff](https://docs.astral.sh/ruff/) to test against a range of Python
style and performance guidelines. You can run the general linting using:
```bash
uv run ruff check
```
You can format the codebase to be compatible using:
```bash
uv run ruff format
```
(The continous integration will test that the code is correctly formatted using
the `--check` flag.)
- We use [Mypy](https://mypy.readthedocs.io/en/stable/) to check the type
correctness of the codebase (for as far as possible). You can run the type
checking using:
```bash
uv run mypy .
```

<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/MiniZinc/minizinc-python/issues) for a
list of proposed features (and known issues).


<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to
be learn, inspire, and create. Any contributions you make are **greatly
appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


<!-- LICENSE -->
## License

Distributed under the Mozilla Public License Version 2.0. See `LICENSE` for more information.


<!-- CONTACT -->
## Contact
👤 **Jip J. Dekker**
  * Twitter: [@DekkerOne](https://twitter.com/DekkerOne)
  * Github: [Dekker1](https://github.com/Dekker1)

🏛 **MiniZinc**
  * Website: [https://www.minizinc.org/](https://www.minizinc.org/)

<!-- ACKNOWLEDGEMENTS -->
<!-- ## Acknowledgements -->

<!-- * []() -->
<!-- * []() -->
<!-- * []() -->

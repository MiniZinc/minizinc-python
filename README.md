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
    <a href="https://minizinc-python.readthedocs.io/en/latest/"><strong>Explore the docs »</strong></a>
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
requires [MiniZinc](https://www.minizinc.org/) 2.5.0+ and
[Python](https://www.python.org/) 3.6.0+ to be installed on the system. MiniZinc
python expects the `minizinc` executable to be available on the executable path,
the `$PATH` environmental variable, or in a default installation location.

_For more information, please refer to the
[Documentation](https://minizinc-python.readthedocs.io/en/latest/)_


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
[Documentation](https://minizinc-python.readthedocs.io/en/latest/)_

<!-- TESTING INSTRUCTIONS -->
## Testing

MiniZinc Python uses [Tox](https://pypi.org/project/tox/) environments to test
its coding style and functionality. The code style tests are executed using
[Black](https://pypi.org/project/black/),
[Flake8](https://pypi.org/project/flake8/), and
[isort](https://pypi.org/project/isort/). The functionality tests are
constructed using the [PyTest]() unit testing framework.

  * To run all tests, simply execute `tox` in the repository directory.
  * Individual environments can be triggered using the `-e` flag.
    * To test the coding style of the repository run `tox -e check`
    * The `py3x` environments are used to test a specific Python version; for
      example, to test using Python version 3.7 run `tox -e py37`

Tox can also be used to generate the documentation, `tox -e docs`, and to
typeset the Python code, `tox -e format`.

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

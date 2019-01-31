Getting Started
===============

This page will guide you through the process of setting up MiniZinc Python. MiniZinc Python requires the following
software to be installed on you machine:

- `MiniZinc <https://www.minizinc.org/>`_ 2.2.3 (or higher)
- `Python <https://www.python.org/>`_ 3.6 (or higher)

..  note::

    MiniZinc is expected to be in its default location. If you are on a Linux machine or changed this location, then you
    will have to ensure that the ``minizinc`` executable is located in a folder in the ``$PATH`` environmental variable.
    When MiniZinc cannot be located, the following warning will be shown: **MiniZinc was not found on the system: no
    default driver could be initialised**. The path can manually be provided using ``find_driver`` function.

Installation
------------

MiniZinc Python can be found on `PyPI <https://pypi.org/project/minizinc/>`_. If you have the ``pip`` package manager
installed, then the simplest way of installing MiniZinc Python is using the following command:

..  code-block:: bash

    $ pip install minizinc

..  note::
    On machines that have both Python 2 and Python 3 installed you might have to use ``pip3`` instead of ``pip``

A basic example
---------------

To test everything is working let's run a basic example. The n-Queens problem is a famous problem within the constraint
programming community. In the MiniZinc Examples we can find the following model for this problem:

..  literalinclude:: examples/nqueens.mzn
    :language: minizinc

The following Python code will use MiniZinc Python to:

1. Load the model from a file (``nqueens.mzn``)
2. Assign the value 4 to ``n``
3. Solve the model using Gecode
4. Print the positions of the Queens store in the array ``q``

..  literalinclude:: examples/nqueens.py
    :language: python

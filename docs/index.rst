MiniZinc Python
===============

..  warning::
    The development of MiniZinc Python is still in the very early stages. We appreciate any feedback for the package,
    but we would recommend refraining from using the package in production software. The package can drastically change
    and backwards compatible changes are not guaranteed.

MiniZinc Python provides a native python interface for the MiniZinc toolchain. The package can interface with MiniZinc
in two ways: using the command line interface, the ``minizinc`` executable, or the experimental C API to MiniZinc that
is currently in development. The main goal of this library is to allow users to use all of MiniZinc's capabilities
directly from Python. This allows you to use MiniZinc in your application, but also enables you to use MiniZinc in new
ways! Using MiniZinc in a procedural language allows you to use incremental solving techniques that can be used to
implement different kinds of meta-heuristics.

Documentation
-------------

This part of the documentation guides you through all of the library’s usage patterns.

..  toctree::
    :maxdepth: 2

    getting_started
    advanced_usage
    library_structure

API Reference
-------------

If you are looking for information on a specific function, class, or method, this part of the documentation is for you.

..  toctree::
    :maxdepth: 2

    api

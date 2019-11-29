MiniZinc Python
===============

MiniZinc Python provides a native python interface for the MiniZinc toolchain.
The package can interface with MiniZinc in two ways: using the command line
interface, the ``minizinc`` executable, or the experimental C API to MiniZinc
that is currently in development. The main goal of this library is to allow
users to use all of MiniZinc's capabilities directly from Python. This allows
you to use MiniZinc in your application, but also enables you to use MiniZinc in
new ways! Using MiniZinc in a procedural language allows you to use incremental
solving techniques that can be used to implement different kinds of
meta-heuristics.

..  note::

    The development of MiniZinc Python is still in its early stages. Although
    the module is fully supported and the functionality is stabilising, we
    will not guarantee that changes made before version 1.0 are backwards
    compatible. Similarly, the functionality of this module is closely
    connected to the releases of the main MiniZinc bundle. An update to this
    module might require an update to your MiniZinc installation.

    Once the project reaches version 1.0, it will abide by `Semantic Versioning
    <https://semver.org>`_. All (breaking) changes are recorded in the
    :ref:`changelog <changelog>`.


Documentation
-------------

This part of the documentation guides you through all of the library’s usage
patterns.

..  toctree::
    :maxdepth: 2

    getting_started
    basic_usage
    library_structure
    advanced_usage

API Reference
-------------

If you are looking for information on a specific function, class, or method,
this part of the documentation is for you.

..  toctree::
    :maxdepth: 2

    api

Changelog
---------

All changes made to this project are recorded in the changelog.

..  toctree::
    :maxdepth: 1

    changelog

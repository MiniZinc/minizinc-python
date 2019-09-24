..  _library-structure: 

Library Structure
=================

Because the library has the ability to interface both using the MiniZinc
executable and a C API, there are various abstraction in the library to make it
more friendly to the user. Unless you need more advanced functionality you will
never directly have to interface with the MiniZinc Driver.

The library is split into three parts. The main Python package contains
everything that is shared between the different drivers and the ``CLI`` and
``API`` packages contain the specific implementations for the executable and the
C API respectively. Once a default driver has been detected the exported
(abstract) classes will be replaced by the specific implementation for the
driver. The specialised versions of classes implement the methods provided by
the abstract classes in the main package. The specialised versions of classes
link back to the MiniZinc Driver for their functionality.

..  seealso::

    The advanced usage guide includes a :ref:`section <multiple-minizinc>` on
    using different and multiple version of MiniZinc at the same time.

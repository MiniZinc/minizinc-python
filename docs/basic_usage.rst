Basic Usage
============

This page provides examples of the basic of MiniZinc Python. It will show
example of the types available in MiniZinc Python and shows how to use features
that are often used.

Using sets
-----------

There are two types in Python that are associated with MiniZinc's sets: ``set``
and ``range``. Generally a set in MiniZinc will be of the type ``set``. For
example, the minizinc set ``{-2, 4, 12}`` will be represented in MiniZinc Python
as ``{-2, 4, 12}`` or ``set([-2, 4, 12])``. However, contiguous sets, like index sets in MiniZinc,
can be more efficiently represented in a ``range`` object, as this only records
the start and end of the set. For example, the MiniZinc set ``-90..310`` is
represented using ``range(-90, 311)`` in MiniZinc Python. When creating a set in
Python, either object can be translated to a MiniZinc set.

..  note::

    The end given Python ``range`` objects is non-inclusive. This means the
    object ``range(1, 3)`` only contains 1 and 2. This is unlike the MiniZinc
    range syntax, which is inclusive. The MiniZinc set ``1..3`` contains 1, 2,
    and 3.

The following example shows how to assign set parameters and how to use the
solutions for set variables.

..  code-block:: python

    from minizinc import Instance, Model, Solver

    gecode = Solver.lookup("gecode")

    model = Model()
    model.add_string(
        """
        include "all_different.mzn";
        set of int: A;
        set of int: B;
        array[A] of var B: arr;
        var set of B: X;
        var set of B: Y;

        constraint all_different(arr);
        constraint forall (i in index_set(arr)) ( arr[i] in X );
        constraint forall (i in index_set(arr)) ( (arr[i] mod 2 = 0) <-> arr[i] in Y );
        """
    )

    instance = Instance(gecode, model)
    instance["A"] = range(3, 8)  # MiniZinc: 3..8
    instance["B"] = {4, 3, 2, 1, 0}  # MiniZinc: {4, 3, 2, 1, 0}

    result = instance.solve()
    print(result["X"])  # range(0, 5)
    assert isinstance(result["X"], range)
    print(result["Y"])  # {0, 2, 4}
    assert isinstance(result["Y"], set)


Using enumerated types
-----------------------

The support for enumerated types in MiniZinc Python is still limited. It is,
however, already supported to assign enumerated types in MiniZinc using a Python
enumeration. When a enumeration is assigned, the values in the solution are
ensured to be of the assigned enumerated type. This is demonstrated in the
following example:

..  code-block:: python

    import enum

    from minizinc import Instance, Model, Solver

    gecode = Solver.lookup("gecode")

    model = Model()
    model.add_string(
        """
        enum DAY;
        var DAY: d;
        constraint d = min(DAY);
        """
    )
    instance = Instance(gecode, model)

    Day = enum.Enum("Day", ["Mo", "Tu", "We", "Th", "Fr"])
    instance["DAY"] = Day

    result = instance.solve()
    print(result["d"])  # Day.Mo
    assert isinstance(result["d"], Day)

Enumerations that are defined in MiniZinc are currently not translated into
Python enumerations. Their values are currently returned as strings. The
following adaptation of the previous example declares an enumerated type in
MiniZinc and contains a string in it's solution.


..  code-block:: python

    from minizinc import Instance, Model, Solver

    gecode = Solver.lookup("gecode")

    model = Model()
    model.add_string(
        """
        enum DAY = {Mo, Tu, We, Th, Fr};
        var DAY: d;
        constraint d = min(DAY);
        """
    )
    instance = Instance(gecode, model)

    result = instance.solve()
    print(result["d"])  # Mo
    assert isinstance(result["d"], str)

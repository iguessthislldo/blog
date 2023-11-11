:tags: python, coding
:created: 2016-10-05T21:45:02.612669+00:00
:published: 2016-10-05T22:14:29.177385+00:00
:summary: Some Python snippets I was apparently proud of

#############################
4 Useful Python Code Snippets
#############################

.. post-info-start

.. card::

    :material-regular:`calendar_month` 2016-10-05
    :material-regular:`sell` :bdg-ref-primary-line:`python <tag-python>` :bdg-ref-primary-line:`coding <tag-coding>`


.. post-info-end

=====================================
Simulate a simple probability outcome
=====================================

It's a really simple function, in fact, it really doesn't need to be a function except for a little convenience.

.. code-block:: python

    from random import uniform

    def chance(p):
        '''Simulates an event with p probability of being true. This is 0 to 1.
        '''
        return p >= uniform(0, 1)

=====================================
An anonymous object (à la Javascript)
=====================================

.. note::

    Update: Use a builtin class like ``types.SimpleNamespace`` or ``collections.namedtuple`` instead of this.

In Javascript, OOP is more unconventional than Python (from a C++ and Java perspective).
Part of this is objects can be created with what is similar to dictionary notation in Python: ``{member: 0, time: "Now"}``.
Also "blank" objects: ``{}``.
What I have here is a shortcut for creating such objects in Python.
I imagine this might be useful in testing of code that handles many different kinds of objects.

.. code-block:: python

    class Anonymous:
        def __init__(self, **attrs):
            for k, v in attrs.items():
                setattr(self, k, v)

        def __repr__(self):
            return '<{}: {}>'.format(self.__class__.__name__, repr(self.__dict__))

        def __str__(self):
            return repr(self)

=================================
See if a Python iterable is empty
=================================

See if a Python iterable (``list``, ``dict``, any object that implements ``__iter__``) is empty.
Unfortunately for a generator this means calling next which may change its state.

.. code-block:: python

    def has_method(obj, method_name):
        '''See if object has a method, should work if its assigned to class or
        to the object itself.
        '''
        return hasattr(obj, method_name) and callable(getattr(obj, method_name))

    def is_empty(obj):
        '''Determines if a iter object is empty. First checks if its a generator,
        then sees if it throws StopIteration the first time. If its not a generator
        then it just checks the length.
        '''
        if not has_method(obj, "__iter__"):
            raise TypeError("obj does not have an __iter__ method")

        if has_method(obj, "__next__"):
            try:
                next(obj)
            except StopIteration:
                return True
            return False
        else:
            return len(obj) == 0

========================================
Set default attributes in a Python class
========================================

This one is my favorite, it is a sort of mini version of `attrs <https://github.com/hynek/attrs>`__ that I made before hearing about it.
It can be used to set default attributes for a class which are overridable from the constructor.

.. code-block:: python

    def defaults(obj, kwargs, **defaults):
        '''Iterate defaults and keyword arguments, set obj attribute to keys and
        their values. Use to set default instance attributes and override them
        with keyword arguments at the same time.
        '''
        for k, v in defaults.items():
            if k not in kwargs:
                setattr(obj, k, v)

        for k, v in kwargs.items():
            if k in defaults:
                setattr(obj, k, v)
            else:
                raise ValueError(
                    '"{}" is not a valid keyword argument to {}'.format(
                        k,
                        obj.__class__.__name__
                    )
                )

An Example:
-----------

.. code-block:: python

    class SomeClass:
        def __init__(self, major_value, **kw):
            self.major_value = major_value
            defaults(self, kw,
                minor_value1 = "Stuff",
                minor_value2 = "Stuff Stuff"
            )

        # ...

    >>> someobj = SomeClass(10)
    >>> someobj.minor_value1
    "Stuff"
    >>> someobj.minor_value2
    "Stuff Stuff"
    >>> anotherobj = SomeClass(11, minor_value2 = "Another Value")
    >>> anotherobj.minor_value2
    "Another Value"

You can of course remove the error checking after ``else: raise ValueError...``, because Python is very flexible and you are free to do whatever.

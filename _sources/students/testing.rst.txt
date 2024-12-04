Testing Drafter Applications
============================

A powerful feature of Drafter is the ability to test your applications.
Drafter functions are simple functions that take in a ``State`` and return a ``Page``.
The ``Page`` object is just a dataclass with a ``state`` and a ``content``, so you can easily inspect the results of
calling your functions, or just write equality assertions.

.. code-block:: python

    from drafter import *
    from bakery import assert_equal

    @dataclass
    class State:
        name: str

    @route
    def index(state: State) -> Page:
        return Page(state, [
            f"Hello, {state.name}!"
        ])

    # ...

    assert_equal(index("World"),
                 Page("World", ["Hello, World!"]))


Automatically Generated Tests
-----------------------------

When you run your Drafter application, Drafter automatically creates tests for you as you interact with the site.

The Debug Information at the bottom of the page includes a section titled **Page Load History**.
Clicking on the **Page Content** arrow will reveal the generated Page content, which can be copy/pasted back as an
``assert_equal`` along with the appropriate **Call**.

You might think of this as "freezing" the expected state of the website, if you are happy with the design.
Subsequent changes to the ``index`` function require us to update these tests, so you do not necessarily want to start
by testing (the way you are usually encouraged to do). But as you make changes, these tests can help you confirm
that the rest of the site still works as originally intended. These are known as **regression tests**.


.. _testing-parts-of-routes:

Testing Parts of Routes
-----------------------

Drafter's automatically generated tests are designed to test the entire result
of a route, including its ``state`` and ``content``. However, sometimes you
want to test just a part of the result, using more relaxed assertions.

To do this, you can manually inspect the result of calling your route, and
then test individual pieces by inspecting the ``state`` and ``content`` of the
resulting ``Page`` object. Remember, the ``Page`` is just a dataclass!

For example, the following allows us to test that the content has at least
some of the expected text:

.. code-block:: python

    from drafter import *
    import random

    @dataclass
    class State:
        name: str

    @route
    def index(state: State) -> Page:
        return Page(state, [
            f"Hello, {state.name}!"
        ])

    # ...

    result = index("World")
    assert_equal("Hello" in result.content, True)

Or you could make an assertion about a specific part of the state, without
reference to any other part of the ``Page``:

.. code-block:: python

    from drafter import *
    import random

    @dataclass
    class State:
        name: str

    @route
    def index(state: State) -> Page:
        return Page(state, [
            f"Hello, {state.name}!"
        ])

    # ...

    result = index("World")
    assert_equal(result.state.name, "World")
.. _help:

=========
More Help
=========

Actions After Start
-------------------

Once you call the ``start_server()`` function, no other code will run until your website finishes.

.. code-block:: python

    from drafter import *

    # These print statements demonstrate when code runs relative to start
    print("This line will execute before the game starts.")
    start_server()
    print("This line will not execute until the game is over."

If you want to have activity in your website, you have to use the ``route`` decorator to add
routes.

Circular Reference Errors
-------------------------

Drafter does its best to automatically generate unit tests for your code. However, it is not
perfect. One particular issue is if you have a *circular reference* in your data.
The unit test will seem to randomly have the text "Circular Reference" in it.

Let's look at an example of how to trigger this issue:

.. code-block:: python

    from drafter import *

    @dataclass
    class Item:
        name: str
        previously_seen: List['Item']

    @dataclass
    class State:
        items: List[Item]

    # ...

    first_item = Item("First Item", [])
    second_item = Item("Second Item", [first_item])
    first_item.previously_seen.append(second_item)
    start_server(State([first_item, second_item]))

In this example, the ``first_item`` has a reference to the ``second_item`` and vice versa.
This creates a circular reference between those elements. When Drafter tries
to generate code to construct the instances, it would get stuck in an infinite loop
trying to flatten everything. Instead, it chooses to generate the text ``"Circular Reference"``.

To fix this issue, you should first confirm that you need circular references.
Circular references are extremely useful for a wide variety of purposes, such
as representing a graph. If you do need them, you can manually write the
unit tests for those cases, using the generated ones as a base.
Capture the result of calling your route, and you can then test
individual pieces by inspecting the ``state`` and ``content`` of the
resulting ``Page`` object. See :ref:`testing-parts-of-routes` for more information.

However, it's also very likely that you do not need circular references,
and you added them by mistake. Review your code carefully to see if you are
accidentally creating circular references. A few ways that this can happen:

- You are appending a list to itself.
- You set the field of an object to itself.
- You have an inner field or list element that refers to the outer object.

For example, if you were


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
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

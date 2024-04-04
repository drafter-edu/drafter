
=====================
Simple Adventure Game
=====================

Now we'll make a little adventure game with multiple pages that link to each other in a more complicated
way, and also an item that you can pick up and use in of the rooms. To make things more exciting, we'll
have images of the screens in the game (generated using ChatGPT).
Preview this website at |adventure_preview|.

.. |adventure_preview| raw:: html

    <a href="https://drafter-edu.github.io/examples/adventure/" target="_blank">
        https://drafter-edu.github.io/examples/adventure/</a>

.. image:: /workbook/part3/screen_shots.png
    :width: 700
    :align: center
    :alt: Screenshot of the Simple Adventure Game

**Step 1: Download** the images and the starting file for the game from the following links:

* :download:`adventure.py </workbook/part3/adventure.py>`
* :download:`field.png </workbook/part3/field.png>`
* :download:`woods.png </workbook/part3/woods.png>`
* :download:`cave.png </workbook/part3/cave.png>`
* :download:`victory.png </workbook/part3/victory.png>`

.. important:: Make sure the files are in the same folder as the python file. You can change the images
    but make sure they have the same filenames, or the tests won't run!

Once again, the number of routes and the number of pages do not match.
The diagram below shows the flow of the game. The game starts with the ``index`` route, where the player
enters their name. The player then moves to the ``small_field`` route, where they can choose to go to the
``woods`` or the ``cave``. In the ``woods`` route, the player can pick up a key, which will allow them to
unlock the door in the ``cave`` route. If the player does not have the key, they will be unable to unlock
the door and will have to leave the cave. The game ends in the ``ending`` route, where the player finds a
treasure chest and wins the game.

.. mermaid::

    flowchart
        start(("Start"))
        index["index"]
        begin[/"begin"/]
        small_field["small_field"]
        woods["woods"]
        check_has_key{has_key}
        check_missing_key{not has_key}
        cave["cave"]
        take_key[/"take_key"/]
        ending["ending"]

        start --> index
        index -- "Begin(name)" --> begin
        begin -.-> small_field
        small_field -- "Woods" --> woods
        small_field -- "Cave" --> cave
        woods --- check_missing_key
        check_missing_key -- "Take key" --> take_key
        take_key -.-> woods
        woods -- "Leave" --> small_field
        check_has_key -- "Unlock door" --> ending
        cave -.- check_has_key
        cave -- "Leave" --> small_field

Notice the diamond shaped nodes in the diagram. These are decision nodes. The game will have two different
paths depending on whether the player has the key or not. The Cave only shows the "Unlock door" button if
the player has the key. The Woods only shows the "Take key" button if the player does not have the key.
This means that you will need an ``if`` statement in your route to decide which content to show.

**Step 2:** Add two fields to the ``State`` class.

* The ``has_key`` field is a boolean
* The ``name`` field is a string

**Step 3:** Finish implementing the following routes:

1. The ``index`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the
   returned ``Page`` will be unchanged. The content of the ``Page`` will be (in order):

    - The text ``"Welcome to the adventure! What is your name?"``
    - A ``TextBox`` that will take the user's ``name`` (the default value is ``"Adventurer"``).
    - A ``Button`` with the text ``"Begin"`` that links to a ``begin`` route.

2. The ``begin`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the
   returned ``Page`` will have the ``name`` field set to the value of the ``TextBox`` in the previous
   page. Use the ``small_field`` route to return the next page, rather than defining a new ``Page`` object.

3. The ``small_field`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the
   returned ``Page`` will be unchanged. The content of the ``Page`` will be (in order):

    - The text ``"You are NAME."`` except replacing ``NAME`` with the value of the ``name`` field in the
      ``State`` object.
    - The text ``"You are in a small field."``
    - The text ``"You see paths to the woods and a cave.``
    - A ``Button`` with the text ``Cave`` that links to the ``cave`` route.
    - A ``Button`` with the text ``Woods`` that links to the ``woods`` route.
    - An ``Image`` with the filename ``"field.png"``.

4. The ``cave`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the
   returned ``Page`` will be unchanged. The content of the ``Page`` will depend on whether or not
   the ``state`` has the ``has_key`` field set to ``True``. If it is is ``True``, then the content
   of the page should be:

    - The text ``"You enter the cave."``
    - The text ``"You see a locked door."``
    - A ``Button`` with the text ``"Unlock door"`` that links to the ``ending`` route.
    - A ``Button`` with the text ``"Leave"`` that links to the ``small_field`` route.
    - An ``Image`` with the filename ``"cave.png"``.

   Otherwise, if the ``has_key`` field is ``False``, then the content of the page should be:

    - The text ``"You enter the cave."``
    - The text ``"You see a locked door."``
    - A ``Button`` with the text ``"Leave"`` that links to the ``small_field`` route.
    - An ``Image`` with the filename ``"cave.png"``.

5. The ``woods`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the
   returned ``Page`` will be unchanged. The content of the ``Page`` will depend on whether or not
   the ``state`` has the ``has_key`` field set to ``True``. If it is is ``True``, then the content
   of the page should be:

    - The text ``"You are in the woods."``
    - A ``Button`` with the text ``"Leave"`` that links to the ``small_field`` route.
    - An ``Image`` with the filename ``"woods.png"``.

   Otherwise, if the ``has_key`` field is ``False``, then the content of the page should be:

    - The text ``"You are in the woods."``
    - The text ``"You see a key on the ground."``
    - A ``Button`` with the text ``"Take key"`` that links to the ``take_key`` route.
    - A ``Button`` with the text ``"Leave"`` that links to the ``small_field`` route.
    - An ``Image`` with the filename ``"woods.png"``.

6. The ``take_key`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the
   returned ``Page`` will have the ``has_key`` field set to ``True``. Use the ``woods`` route to return
   the next page, rather than defining a new ``Page`` object.

7. The ``ending`` route will consume a ``State`` object and return a ``Page``. The ``state`` in the
   returned ``Page`` will be unchanged. The content of the ``Page`` will be:

    - The text ``"You unlock the door.",``
    - The text ``"You find a treasure chest."``
    - The text ``"You win!"``
    - An ``Image`` with the filename ``"victory.png"``.

**Step 4:** Run the application and check the tests to see if you have implemented the routes correctly.

This application showed you how to make multiple pages that link in more complicated ways, including
some pages that had different content depending on the state of the ``State`` object. You also learned
how to use images in your application.

..
    **Interesting extensions:** If you are interested in extending the game, here are some ideas for things
    you might add.

    1. Add a "Play Again" button to the ``ending`` route that links back to the ``index`` route, reseting
       the fields of the ``State`` object.
    2. Add more rooms to the game.
    3. Add more items to the game that can be picked up and used in different rooms. Use a list of strings
       or a list of booleans to manage the inventory.
    4. Add a timer to the game that limits the amount of time the player has to complete the game.
       Keep track either of the current time (using the ``time`` module) or the number of moves the player
       has made.

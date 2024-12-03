.. _quickstart:

--------------------------
Drafter Quick Start Guide
--------------------------
Drafter is an educational web development library for Python. What does that mean?

As a student, you can use Drafter to learn and practice Python by creating a full-stack website.

Let's look at some code to get us started.

Once you've installed Drafter, you only need two lines of code to get started:

.. code-block:: python
    :linenos:

    from drafter import *

    start_server()

These two lines of code should yield a result like this:

.. code-block::

    Drafter server starting up (using Bottle backend).
    Listening on http://localhost:8080/

    Hit Ctrl-C to quit.

If you visit the url `http://localhost:8080/ <http://localhost:8080/>`_ then you will see a page like this:

.. image:: quickstart_empty_site.png
    :width: 700
    :alt: Simple website with the text "Hello World!" and "Welcome to Drafter" along with some more information further below.

The top rectangle is the content of your website, which defaults to the message "Hello World!" and "Welcome to Drafter".
Down below, you see some debug information that will be helpful once we start adding more to our site.
For now, you can see that we have a single, default **Route**.

===========
0. Overview
===========

Web servers connect URLs to webpages via routes.
We need to begin by creating a **route**, a function that returns a **Page**.
Each route will correspond to a URL ("uniform resource locator") that uniquely describes a page of the website.
When you visit a URL, the routed function is called and the resulting page is displayed to the user.
These pages will have links to other URLs in the same web server.

Another useful feature of a server is that **State** can be saved between pages.
The value from a textbox on the first page can be saved and shown on the second page.
A good way to create State in Drafter is to make a dataclass.

.. code-block:: python
    :emphasize-lines: 2-6
    :linenos:

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        message: str

    start_server(State("The original message"))


The code above does not result in a visible change, because we have not created any new routes that take advantage of
the state.
Let's make a new route function that can show off the state.

.. code-block:: python
    :emphasize-lines: 8-13
    :linenos:

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        message: str

    @route
    def index(state: State) -> Page:
        return Page(state, [
            "The message is:",
            state.message
        ])

    start_server(State("The original message"))

The new ``index`` function has a decorator (``@route``), just like the dataclass from before.
This decorator adds in the functionality to connect the function to a URL.
The name ``index`` is special, making this function the "default" webpage that will be shown.

As a route, the function must return a ``Page``. The ``Page`` dataclass constructor is provided by Drafter
and has two parameters: the new state of the page and a list of strings that will be displayed on the webpage.
In this case, the webpage will have two lines of text: "The message is:" and "The original message".
We usually will keep passing in the same state, and just update the state's values mutably.

After you add the code above, you will need to stop the original server and start the new one.
If you visit the url `http://localhost:8080/ <http://localhost:8080/>`_ then you will see a page like this:

.. image:: quickstart_simple_state.png
    :width: 700
    :alt: Simple website with the text "The message is" and "The original message" along with some more information further below.


================
1. Another Route
================

We can see the state now, but the state is *static* - nothing ever changes. Let's add in another page that changes
the state.

.. code-block:: python
    :emphasize-lines: 15-21
    :linenos:

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        message: str

    @route
    def index(state: State) -> Page:
        return Page(state, [
            "The message is:",
            state.message
        ])

    @route
    def change_message(state: State) -> Page:
        state.message = "The new message!"
        return Page(state, [
            "Now the message is",
            state.message
        ])

    start_server(State("The original message"))


We've created a new route named ``change_message``, we could actually visit if we changed the URL in the web
browser. However, that's inconvenient for users. Instead, we can add a link to the ``index`` page to make it easier
for them to navigate there. We can do this easily by just providing a button.

.. code-block:: python
    :emphasize-lines: 13
    :linenos:

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        message: str

    @route
    def index(state: State) -> Page:
        return Page(state, [
            "The message is:",
            state.message,
            Button("Change the Message", change_message)
        ])

    @route
    def change_message(state: State) -> Page:
        state.message = "The new message!"
        return Page(state, [
            "Now the message is",
            state.message
        ])

    start_server(State("The original message"))

Stopping the old server and running this new one will show that there is a button on the new page.

.. image:: quickstart_button_state_1.png
    :width: 700
    :alt: Clickable button is now visible on the original page

Once we click the button, we are taken to the new page.


.. image:: quickstart_button_state_2.png
    :width: 700
    :alt: Clickable button was added on the first page that leads to this new page.

Note that the State has changed and there is now a new item in the Page Load History.
This state is not very exciting, though, so maybe we can provide the user with an opportunity to change the message too?

===============
2. Taking Input
===============

Let's add a TextBox to the ``change_message`` page. This is a **Component**, just like the Button we added before.

.. code-block:: python
    :emphasize-lines: 22-23
    :linenos:

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        message: str

    @route
    def index(state: State) -> Page:
        return Page(state, [
            "The message is:",
            state.message,
            Button("Change the Message", change_message)
        ])

    @route
    def change_message(state: State) -> Page:
        state.message = "The new message!"
        return Page(state, [
            "Now the message is",
            state.message,
            "Would you like to change the message?",
            TextBox("new_message", state.message)
        ])

    start_server(State("The original message"))

The first argument to the ``TextBox`` constructor call is the name of the field, which will be necessary to use the value from the field later on.
The second argument is the default value of the ``TextBox`` when the page displays, which should be the current message's value.
To actually use whatever value the user ends up typing into the box, we need to create a new Button and a new route function.

.. code-block:: python
    :emphasize-lines: 24, 27-30
    :linenos:

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        message: str

    @route
    def index(state: State) -> Page:
        return Page(state, [
            "The message is:",
            state.message,
            Button("Change the Message", change_message)
        ])

    @route
    def change_message(state: State) -> Page:
        state.message = "The new message!"
        return Page(state, [
            "Now the message is",
            state.message,
            "Would you like to change the message?",
            TextBox("new_message", state.message),
            Button("Save", set_the_message)
        ])

    @route
    def set_the_message(state: State, new_message: str) -> Page:
        state.message = new_message
        return index(state)

    start_server(State("The original message"))

Now, when the user clicks the ``Save`` button, they will be taken to the ``set_the_message`` URL.
That route function takes a parameter named ``new_message``, which matches the name of the field we created in ``change_message``.
Drafter will translate the data from the box to the page, and we use that to update the ``state``.

In the ``return`` statement of ``set_the_message``, we call the ``index`` function to reuse its logic for rendering the basic page.
We could have instead created a new page that linked back to the original ``index`` page - the design was really up to us.

.. image:: quickstart_string_state.png
    :width: 700
    :alt: A textfield with a save button next to it

Rerunning the site will allow you to change the message dynamically.
But the site is still not very engaging.
Let's add some more interactivity.

=====================
3. More Interactivity
=====================

We're going to create another page, which will have two possible images, controlled by a CheckBox.
First, we create the new page.

.. code-block:: python
    :emphasize-lines: 14-15, 34-39
    :linenos:

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        message: str

    @route
    def index(state: State) -> Page:
        return Page(state, [
            "The message is:",
            state.message,
            Button("Change the Message", change_message),
            "You can use the button below to go see a picture",
            Button("View the picture", view_picture)
        ])

    @route
    def change_message(state: State) -> Page:
        state.message = "The new message!"
        return Page(state, [
            "Now the message is",
            state.message,
            "Would you like to change the message?",
            TextBox("new_message", state.message),
            Button("Save", set_the_message)
        ])

    @route
    def set_the_message(state: State, new_message: str) -> Page:
        state.message = new_message
        return index(state)

    @route
    def view_picture(state: State) -> Page:
        return Page(state, [
            Image("https://placedog.net/500/280?random"),
            Button("Return to the main page", index)
        ])

    start_server(State("The original message"))

We've now created a new page where an image of a dog will appear.
There is also a button to take the user back to the original page.

What if users don't like dogs? It's a possiblity that we want to prepare for.
We can provide a CheckBox to control whether they encounter a picture of a dog or not.
We will want to remember the decision of whether they see a dog when we return to the index, so it's
important that we store this as part of the State.

.. code-block:: python
    :emphasize-lines: 7, 15-16, 38-43, 45
    :linenos:

    from drafter import *
    from dataclasses import dataclass

    @dataclass
    class State:
        message: str
        likes_dogs: bool

    @route
    def index(state: State) -> Page:
        return Page(state, [
            "The message is:",
            state.message,
            Button("Change the Message", change_message),
            "Are you okay seeing pictures of dogs?",
            CheckBox("are_dogs_okay", state.likes_dogs),
            "You can use the button below to go see a picture",
            Button("View the picture", view_picture)
        ])

    @route
    def change_message(state: State) -> Page:
        state.message = "The new message!"
        return Page(state, [
            "Now the message is",
            state.message,
            "Would you like to change the message?",
            TextBox("new_message", state.message),
            Button("Save", set_the_message)
        ])

    @route
    def set_the_message(state: State, new_message: str) -> Page:
        state.message = new_message
        return index(state)

    @route
    def view_picture(state: State, are_dogs_okay: bool) -> Page:
        if are_dogs_okay:
            url = "https://placedog.net/500/280?random"
        else:
            url = "https://placekitten.com/500/280?random"
        state.likes_dogs = are_dogs_okay
        return Page(state, [
            Image(url),
            Button("Return to the main page", index)
        ])

    start_server(State("The original message", True))

Now we have a new field in our state named ``likes_dogs``.
We must not only update the dataclass definition, but also the initial value in the constructor.

Separately, we also have a ``CheckBox`` in the ``index``. The first argument is the name of the
checkbox, which will become a parameter in the ``view_picture`` function. The second argument is
the current value of the checkbox, which comes from our state.

In the ``view_picture`` function, we take the ``are_dogs_okay`` parameter (a boolean, since it
came from a checkbox) and use it to decide which URL we show.
We also update the ``state.likes_dogs`` field; this will make sure that when the user returns to the
index page, their decision is retained.

We've added a lot of features to our website, and testing the entire site takes a lot of clicking.
It's time to setup some tests, so we can make sure the website is working correctly even as we change parts.

==========
4. Testing
==========

Drafter works perfectly well with the Bakery library to write ``assert_equal`` statements.
We can call a route function and check that the produced ``Page`` matches the expected result.
This does require writing fairly lengthy statements, though:

.. code-block:: python
    :emphasize-lines: 3, 50-70
    :linenos:

    from drafter import *
    from dataclasses import dataclass
    from bakery import assert_equal

    @dataclass
    class State:
        message: str
        likes_dogs: bool

    @route
    def index(state: State) -> Page:
        return Page(state, [
            "The message is:",
            state.message,
            Button("Change the Message", change_message),
            "Are you okay seeing pictures of dogs?",
            CheckBox("are_dogs_okay", state.likes_dogs),
            "You can use the button below to go see a picture",
            Button("View the picture", view_picture)
        ])

    @route
    def change_message(state: State) -> Page:
        state.message = "The new message!"
        return Page(state, [
            "Now the message is",
            state.message,
            "Would you like to change the message?",
            TextBox("new_message", state.message),
            Button("Save", set_the_message)
        ])

    @route
    def set_the_message(state: State, new_message: str) -> Page:
        state.message = new_message
        return index(state)

    @route
    def view_picture(state: State, are_dogs_okay: bool) -> Page:
        if are_dogs_okay:
            url = "https://placedog.net/500/280?random"
        else:
            url = "https://placekitten.com/500/280?random"
        state.likes_dogs = are_dogs_okay
        return Page(state, [
            Image(url),
            Button("Return to the main page", index)
        ])

    assert_equal(index(State("My message", True)),
                 Page(State("My message", True), [
                    "The message is:",
                    "My message",
                    Button("Change the Message", change_message),
                    "Are you okay seeing pictures of dogs?",
                    CheckBox("are_dogs_okay", True),
                    "You can use the button below to go see a picture",
                    Button("View the picture", view_picture)
                 ]))

    assert_equal(set_the_message(State("My message", True), "New message"),
                 Page(State("New message", True), [
                    "The message is:",
                    "New message",
                    Button("Change the Message", change_message),
                    "Are you okay seeing pictures of dogs?",
                    CheckBox("are_dogs_okay", True),
                    "You can use the button below to go see a picture",
                    Button("View the picture", view_picture)
                 ]))

    start_server(State("The original message", True))

These two ``assert_equal`` statements check the ``index`` and ``set_the_message`` functions.
Those functions take in the current state (which we are free to make up).
The ``set_the_message`` function also takes in a Boolean argument (whether the user wants dog photos).
Both functions return a ``Page``, which has the new resulting state and a list of the page content.

Getting the exact values correct can be tricky, but fortunately there is a way to simplify the process a little.
The Debug Information at the bottom of the page includes a section titled **Page Load History**.
Clicking on the **Page Content** arrow will reveal the generated Page content, which can be copy/pasted back as an
``assert_equal`` along with the appropriate **Call**.

.. image:: quickstart_copy_page_content.png
    :width: 700
    :alt: The page content expandable

You might think of this as "freezing" the expected state of the website, if you are happy with the design.
Subsequent changes to the ``index`` function require us to update these tests, so you do not necessarily want to start
by testing (the way you are usually encouraged to do). But as you make changes, these tests can help you confirm
that the rest of the site still works as originally intended.

============
5. Moving On
============

So now you have a very simple site. Here are some ideas for additions and extensions you can make:

1. Add more state and routes to the site, so that there are more pages.
2. Add another page with a numeric field (hint: you will need to check that the user entered text `isnumeric` and then convert it to an integer).
3. Use the `SelectBox` to make a dropdown list with several options.
4. Use the `NumberedList` or `BulletedList` to represent a list of values, and then use the `append` method to add a new item via a button.

Check out the :ref:`documentation of Components <fulldocs>` to see all that you can
add to your website!

And if you want a longer example, check out the :ref:`calculator example <calculator>` to see a more complicated web application.

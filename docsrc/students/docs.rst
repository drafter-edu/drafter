.. _fulldocs:

Drafter Documentation for Students
===================================

Basic Routing
-------------

.. _route:

.. decorator:: route
               route(url)

    Decorator to turn a function into route connected to a URL. If the `url` is not given, then
    the function's name will be used as the route. Unless the name of the function is `index`, in which
    case that route will be used as the index of the website (the front, default page).

    :param url: The URL to connect to the function as a route. Defaults to function's name, if not given.
    :type url: str

Pages
-----

.. function:: Page(state, content)

    Constructor function for the ``Page`` object, which holds all the information for a viewable web page.
    The `state` is hidden from the user, but the `content` is rendered into HTML.
    This should be returned from any `route` function.

    The `content` is a list of either string values or `Component` instances. The strings can contain actual
    HTML, which will be injected directly into the page. The `Component` instances will also be turned into HTML.

    :param state: The new value of the page, hidden from the user. This is usually an instance of a dataclass.
        If there is no change to the state, then will just be the `state` parameter.
    :param content: The actual content of the page, eventually rendered as HTML in the browser. Can combine both
        string values and `Component` instances.
    :type content: list[str | Component]

Server Control
--------------

.. function:: start_server()
              start_server(inital_state)

    Function to start the server and launch the website. The local URL of the server will be displayed,
    usually defaulting to `http://localhost:8080/ <http://localhost:8080/>`_. No code will be executed
    after this call.

    The `initial_state` should match the type of the first parameter for every route. If no `initial_state` is given,
    then the state will initially be `None`.

    :param initial_state: The initial state of the website, usually a dataclass instance. Defaults to `None`.


Components
----------

.. function:: Image(url)
              Image(url, width, height)

    An image

.. function:: Link(text, url)

    A link

.. function:: TextBox(name)
              TextBox(name, default_value)

    A text box

.. function:: TextArea(name)
              TextArea(name, default_value)

    A multiline text area

.. function:: SelectBox(name, options)
              SelectBox(name, options, default_value)

    A dropdown box

.. function:: CheckBox(name)
              CheckBox(name, default_value)

    A check box


.. function:: LineBreak()

    A line break

.. function:: HorizontalRule()

    A horizontal line stretching across the page

.. function:: Button(text, url)

    A clickable button

.. function:: NumberedList(items)

    A numeric, ordered list

.. function:: BulletedList(items)

    An unordered, enumerated list

.. function:: Header(body)
              Header(body, level)

    A text header of different sizes.

.. function:: Table(data)

    A tabular representation of data.


Debug Information
-----------------

.. function:: show_debug_information()

    Show the debug information at the bottom.

.. function:: hide_debug_information()

    Hide the debug information at the bottom.

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

    An image to be displayed on the page. Usually needs to be a complete URL, including the `http://` or `https://`.
    Note that some websites may not allow you to use their images on your website, so be careful; you may want to
    rehost the image somewhere more reliable.

    If you know the exact size of the image, you can specify it with the `width` and `height` parameters. Otherwise,
    the page may resize while the image is being loaded.

    :param url: The URL of the image.
    :type url: str
    :param width: The width of the image, in pixels. Defaults to `None`, which will use the image's default width.
    :type width: int
    :param height: The height of the image, in pixels. Defaults to `None`, which will use the image's default height.
    :type height: int

.. function:: Link(text, url)

    A link to another page. The `text` is what will be displayed on the page, and the `url` is where the link will take
    you. This gets rendered as a normal HTML link (underlined blue text). If you want to use a button instead, use the
    `Button` component.

    :param text: The text to display for the link.
    :type text: str
    :param url: Either a string representing the full URL you are linking to (possibly external to the server) or the
                name of a function that is a route on the server (without quotes or calling parentheses).
    :type url: str or function

.. function:: TextBox(name)
              TextBox(name, default_value)

    A text box for the user to enter text. The `name` is the name of the text box, which will be used to identify
    the text box when the user submits the form (and becomes a parameter to the linked page). The
    `default_value` is the initial value of the text box, which will be displayed to the user. If no `default_value`
    is provided, the textbox will initially be empty.

    :param name: The name of the text box, which will be used to identify the text box when the user submits the form.
                 Make sure this is a valid Python identifier (start with a letter followed only by letters, numerals,
                 and underscores). This must match the same parameter name in the corresponding linked route.
    :type name: str
    :param default_value: The initial value of the text box, which will be displayed to the user. Defaults to `None`,
                          which will make the text box initially empty.
    :type default_value: str

.. function:: TextArea(name)
              TextArea(name, default_value)

    A multiline text area for the user to enter text. Basically the same as the `TextBox` component, but with multiple
    lines. The `name` is the name of the text area, which will be used to identify
    the text area when the user submits the form (and becomes a parameter to the linked page). The
    `default_value` is the initial value of the text area, which will be displayed to the user. If no `default_value`
    is provided, the text area will initially be empty.

    :param name: The name of the text area, which will be used to identify the text area when the user submits the form.
                 Make sure this is a valid Python identifier (start with a letter followed only by letters, numerals,
                 and underscores). This must match the same parameter name in the corresponding linked route.
    :type name: str
    :param default_value: The initial value of the text area, which will be displayed to the user. Defaults to `None`,
                          which will make the text area initially empty.
    :type default_value: str

.. function:: SelectBox(name, options)
              SelectBox(name, options, default_value)

    A dropdown box for the user to select a single option. The `name` is the name of the dropdown box, which will be used
    to identify the dropdown box when the user submits the form (and becomes a parameter to the linked page). The
    `options` is a list of strings representing the options in the dropdown box. The `default_value` is the initial
    value of the dropdown box, which will be displayed to the user. If no `default_value` is provided, the dropdown box
    is probably the first element of the list, or the last one, or maybe blank.

    These boxes are also sometimes called combo boxes, dropdowns, or select lists.

    :param name: The name of the select box, which will be used to identify the select box when the user submits the form.
                 Make sure this is a valid Python identifier (start with a letter followed only by letters, numerals,
                 and underscores). This must match the same parameter name in the corresponding linked route.
    :type name: str
    :param options: The list of options to display in the select box. Each option should be a string.
    :type options: list[str]
    :param default_value: The initial value of the select box, which will be displayed to the user. Defaults to `None`,
                          which will make the select box initially empty.
    :type default_value: str

.. function:: CheckBox(name)
              CheckBox(name, default_value)

    A check box for the user to select. The `name` is the name of the check box, which will be used to identify the
    check box when the user submits the form (and becomes a parameter to the linked page). The `default_value` is the
    initial value of the check box, which will be displayed to the user. If no `default_value` is provided, the check
    box will initially be unchecked.

    :param name: The name of the check box, which will be used to identify the check box when the user submits the form.
                 Make sure this is a valid Python identifier (start with a letter followed only by letters, numerals,
                 and underscores). This must match the same parameter name in the corresponding linked route.
    :type name: str
    :param default_value: The initial value of the check box, which will be displayed to the user. Defaults to `None`,
                          which will make the check box initially unchecked.
    :type default_value: bool


.. function:: LineBreak()

    A line break in the page. This is a single line break, forcing a new line on the page. It is the same as the
    HTML ``<br>`` tag.

.. function:: HorizontalRule()

    A horizontal line stretching across the page. This is the same as the HTML ``<hr>`` tag.

.. function:: Button(text, url)

    A clickable button on the page. The `text` is what will be displayed on the button, and the `url` is where the
    button will take you. This gets rendered as a normal HTML button. All of the input fields on the page will be
    submitted with the button press, and passed as parameters to the linked page.

    :param text: The text to display for the button.
    :type text: str
    :param url: Either a string representing the full URL you are linking to (possibly external to the server) or the
                name of a function that is a route on the server (without quotes or calling parentheses).
    :type url: str or function

.. function:: NumberedList(items)

    A numeric, ordered list of items. The `items` is a list of strings, each of which will be a separate item in the
    list. This gets rendered as a normal HTML ordered list.

    :param items: The list of items to display in the ordered list. Each item should be a string. If they are not
                  strings, then they will be converted using the builtin ``str`` function.
    :type items: list[str]

.. function:: BulletedList(items)

    An unordered, enumerated list. The `items` is a list of strings, each of which will be a separate item in the
    list. This gets rendered as a normal HTML unordered list.

    :param items: The list of items to display in the unordered list. Each item should be a string. If they are not
                  strings, then they will be converted using the builtin ``str`` function.
    :type items: list[str]

.. function:: Header(body)
              Header(body, level)

    A text header of different sizes. The `body` is the text to display in the header. The `level` is the size of the
    header, with 1 being the largest and 6 being the smallest. If no `level` is given, then it will default to 1.

    :param body: The text to display in the header.
    :type body: str
    :param level: The size of the header, with 1 being the largest and 6 being the smallest. Defaults to 1.
    :type level: int

.. function:: Table(data)

    A tabular representation of data. The `data` is a list of lists, where each inner list is a row in the table.
    The `data` can also be a list of dataclass instances, which will be rendered as a pleasant table. If a single
    dataclass is passed in, that will be rendered with the fields as rows in the table.

    :param data: The data to display in the table. Each row should be a list of strings, list of dataclass instances,
                 or a single dataclass instance.
    :type data: list[list[str]] or list[object] or object


Debug Information
-----------------

.. function:: show_debug_information()

    Show the debug information at the bottom, including the current route, current state, the list of available routes,
    and the history of visited pages.

.. function:: hide_debug_information()

    Hide the debug information at the bottom.

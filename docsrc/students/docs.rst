.. _fulldocs:

Drafter Documentation for Students
===================================

This is the Student documentation for the Drafter web framework.
This file is organized into the following sections:

1. `Basic Routing`_: How to create routes and pages for your website.
2. `Server Control`_: How to start the server and launch the website.
3. `Components`_: The different components you can use to build your pages.
4. `Debug Information`_: How to show and hide the debug information at the bottom of the page.

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
              start_server(initial_state, port=8080)

    Function to start the server and launch the website. The local URL of the server will be displayed,
    usually defaulting to `http://localhost:8080/ <http://localhost:8080/>`_. No code will be executed
    after this call.

    The `initial_state` should match the type of the first parameter for every route. If no `initial_state` is given,
    then the state will initially be `None`.

    For more details, refer to the :py:func:`drafter.server.start_server`

    :param initial_state: The initial state of the website, usually a dataclass instance. Defaults to `None`.
    :param port: The port to run the server on. Defaults to `8080`.

.. _components_detailed:

Components
----------

.. function:: Image(url)
              Image(url, width, height)

    An image to be displayed on the page. Usually needs to be a complete URL, including the `http://` or `https://`.
    Note that some websites may not allow you to use their images on your website, so be careful; you may want to
    rehost the image somewhere more reliable.

    If you know the exact size of the image, you can specify it with the `width` and `height` parameters. Otherwise,
    the page may resize while the image is being loaded.

    :param url: The URL of the image, or filename of the image as a string (in quotes) if it is in the same folder as the code.
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
              Button(text, url, arguments)

    A clickable button on the page. The `text` is what will be displayed on the button, and the `url` is where the
    button will take you. This gets rendered as a normal HTML button. All of the input fields on the page will be
    submitted with the button press, and passed as parameters to the linked page.

    :param text: The text to display for the button.
    :type text: str
    :param url: Either a string representing the full URL you are linking to (possibly external to the server) or the
                name of a function that is a route on the server (without quotes or calling parentheses).
    :type url: str or function
    :param arguments: Any additional arguments to pass to the server when the button is pressed. These should be
                      ``Argument`` instances. Defaults to an empty list.
    :type arguments: list[Argument]

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

.. function:: Span(...components)

    A span of text with multiple components. The `components` can be any number of strings or `Component` instances,
    which will be rendered in the span. This is useful for combining multiple components into a single line.

    :param components: The components to display in the span. Each component should be a string or a `Component`
                       instance. You do not pass them in as a list, but as separate arguments (like the ``print``)
                       function.
    :type components: str | Component

.. function:: Argument(name, value)

    A hidden argument to be passed to the server. The `name` is the name of the argument, and the `value` is the value.
    You can only use strings, integers, floats, or booleans as values. This is useful for passing information to the
    server without displaying it to the user.

    A major use for this feature is as an additional parameter to buttons. If you want to pass additional information
    to the server when a button is pressed, you can use this component to do so.

    .. code-block:: python

        Button("Submit", some_route, Argument("additional_info", "extra_data"))

    Note that buttons must have unique names, or the arguments will not be distinguishable.

    :param name: The name of the argument, which will be used to identify the argument when the user submits the form.
                 Make sure this is a valid Python identifier (start with a letter followed only by letters, numerals,
                 and underscores).
    :type name: str

    :param value: The value of the argument, which will be passed to the server. This can be a string, integer, float,
                  or boolean.
    :type value: str | int | float | bool

.. function:: MatPlotLibPlot()
              MatPlotLibPlot(extra_matplotlib_settings: dict)

    A plot generated by MatPlotLib. This will render a plot on the page, using the MatPlotLib library. This is useful
    for displaying graphs, charts, and other visual data.

    This is essentially a drop-in replacement for the MatPlotLib ``show`` function, which will not work in a web
    environment. Instead of calling ``show``, you can call this component and put it in the content of the page.

    You can pass a dictionary to the component, which will be passed to the MatPlotLib ``savefig`` function, e.g.,
    to adjust the plot format or size. However, the normal MatPlotLib functions will work normally, so you can adjust
    the plot as you normally would using the ``plt.*`` functions.

    .. code-block:: python

        import matplotlib.pyplot as plt

        @route
        def plot_page(state: State) -> Page:
            plt.plot([1, 2, 3, 4])
            plt.ylabel('some numbers')
            plt.title("A Plot")
            return Page(state, [
                "Plot:",
                MatPlotLibPlot()
            ])

.. function:: Download(text, filename, contents)
              Download(text, filename, contents, content_type)

    A download link for the user to download a file. The ``text`` is what will be displayed for the link, the ``filename``
    is the name of the file that will be downloaded, and the ``contents`` is the actual contents of the file. The
    ``content_type`` is the MIME type of the file, which will be used to determine how the file is downloaded. If no
    ``content_type`` is given, then it will default to ``text/plain``.

    This is useful for allowing users to download files from your website, such as PDFs, images, or other data.
    For example, you might generate a text file and allow the user to download it.

    .. code-block:: python

        Download("Download File", "file.txt", "This is the contents of the file.")

    Or a JSON file:

    .. code-block:: python

        import json
        data = [1, 2, 4, "hello", {"key": "value"}]
        Download("Download JSON", "data.json", json.dumps(data), "application/json")

    External hyperlinks are supported too.
    If you want to have them download a URL of a video, for example, you could do:

    .. code-block:: python

        Download("Download Video", "video.mp4", "http://example.com/video.mp4", "video/mp4")

    Local files are not automatically provided, though. If you want to provide a local file, you will need to read the
    file and provide the contents as a string.

    You can find a list of common MIME types `here <https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types>`_.

    :param text: The text to display for the download link.
    :type text: str
    :param filename: The name of the file that will be downloaded.
    :type filename: str
    :param contents: The contents of the file that will be downloaded. This should be a string.
    :type contents: str
    :param content_type: The MIME type of the file. Defaults to ``text/plain``.
    :type content_type: str

.. function:: Div(...components)
              Row(...components)

    A division or row of components. The `components` can be any number of strings or `Component` instances, which will
    be rendered in the division or row. This is useful for grouping multiple components together.

    :param components: The components to display in the division or row. Each component should be a string or a `Component`
                       instance. You do not pass them in as a list, but as separate arguments (like the ``print``)
                       function.
    :type components: str | Component

.. function:: PreformattedText(text)

        Preformatted text to display on the page. The `text` is the text to display, which will be rendered in a monospaced
        font. This is useful for displaying code, logs, or other text that needs to be displayed exactly as it is written.

        :param text: The text to display in the preformatted text. This will be rendered in a monospaced font.
        :type text: str

.. function:: FileUpload(name)
              FileUpload(name, accept)

    A file upload component for the user to upload a file. The `name` is the name of the file upload component, which will
    be used to identify the file when the user submits the form (and becomes a parameter to the linked page).

    Be mindful of the target type of the parameter. If the file is regular text, then the parameter should be a ``str``;
    if the file is binary data, then the parameter should be a ``bytes``.
    If you are accepting an image (e.g., ``FileUpload("new_image", "image/*")``), then you can use the `PIL` library to
    convert the image to a format that can be displayed on the page. If you can trust the user to upload only images,
    then you can make the parameter a ``PIL.Image`` object; otherwise you should leave the parameter as a ``bytes``
    and convert the image to a displayable format in the route.

    The `accept` parameter is a string representing the file types that the user can upload. This should be a comma-separated
    list of MIME types, such as ``"image/*,.pdf"``. If no `accept` is given, then the user can upload any file type.
    You can also pass a list of strings, which will be joined with commas.

    :param name: The name of the file upload component, which will be used to identify the file when the user submits the form.
                 Make sure this is a valid Python identifier (start with a letter followed only by letters, numerals,
                 and underscores). This must match the same parameter name in the corresponding linked route.
    :type name: str
    :param accept: The file types that the user can upload. This should be a comma-separated list of MIME types.
                   Defaults to `None`, which will allow the user to upload any file type.
    :type accept: str | list[str]


Debug Information
-----------------

.. function:: show_debug_information()

    Show the debug information at the bottom, including the current route, current state, the list of available routes,
    and the history of visited pages.

.. function:: hide_debug_information()

    Hide the debug information at the bottom.

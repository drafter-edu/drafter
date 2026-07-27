.. _llms:

Gemini Support
==============

If you're interested in using Gemini in Drafter, then you'll have to do some setup.

A key limitation of Drafter, when deployed through GitHub Actions, is that it cannot directly
access private LLMs or APIs that require authentication. To work around this, you can set
up a proxy server that handles requests to the LLM on behalf of Drafter. This actually can work
with any LLM that provides an HTTP API, not just Gemini, and can be adapted for other deployment
platforms and backends as well.

Note that this is NOT officially supported by Drafter, and you'll need to manage the proxy server
yourself. There are security implications to consider, especially if you're dealing with sensitive data.
This approach does not ensure any kind of authentication or authorization for requests made to the LLM;
anyone who can access the proxy server can potentially make requests to the LLM using your API key.
Generally, this is not recommended for production use. Use at your own risk!

Deploy Your Site
----------------

Before setting up the proxy server, ensure that your Drafter site is deployed using GitHub Actions.
Follow the steps in the "Deploying with GitHub Actions" section of the Drafter documentation: :ref:`deployment`.

Note the URL of your deployed site. You will need the origin (protocol + domain) for configuring the proxy server.
For example, if your site is deployed at ``https://ud-f25-cs1.github.io/my-site-name``, the origin is
``https://ud-f25-cs1.github.io``.


Get Your Gemini API Key
-----------------------

To use Gemini, you'll need an API key from Google Cloud: https://aistudio.google.com/api-keys

Use the "Create API Key" button to generate a new API key. Make sure to keep this key secure and do not share it publicly.

The key will look something like ``AIzaSyAeFylvq4swfvDPKuacQVZGq0oYWsGlwI4``, which is just an example and not a real key.

.. danger::

    Never expose your API keys or sensitive information in client-side code or code repositories.
    Definitely do NOT include your API keys directly in your Drafter site code or GitHub repository.
    If you accidentally leak the key, make sure you delete it and generate a new one!


Setting Up a Proxy Server
-------------------------

You are going to create a **CloudFlare Worker** that will act as the proxy server.

CloudFlare is a platform that provides various web services, including specialized functions called "Workers"
that can run JavaScript code without requiring you to manage your own server infrastructure.


1. Create a CloudFlare account using your GitHub account: https://dash.cloudflare.com/login

2. On the left sidebar, click on "Workers & Pages".

3. Click on "Create application" and select "Start with Hello World!".

4. Set the Worker name to something descriptive like "drafter-gemini-proxy".

5. Click "Deploy".

6. Once the worker is created, click the "Settings" tab in the top menu of the screen (right of the "Overview").

7. Look for the section titled "Variables and Secrets" and click on the "+ Add" button to the right.

8. Add a new Text variable with the Variable name ``GEMINI_API_KEY`` and set its value to your Gemini API key.

9. Click the blue arrow button next to the "Deploy" button to choose "Save version".

10. Click the "Edit code" button in the top-right corner.

11. In the editor that appears, replace the default code with the following code snippet:

.. literalinclude:: cloudflare_worker.js
    :language: javascript
    :linenos:
    :emphasize-lines: 13

12. Edit line 13 (highlighted above) to be the origin of your deployed Drafter site
   (e.g., ``https://ud-f25-cs1.github.io``).

13. Click the blue "Deploy" button in the top-right corner to save and deploy your changes.

14. You can click the "Visit" button next to the "Deploy" button, but that will most likely show a page that
    only says "Forbidden". That's expected, since the worker is not meant to be accessed directly.
    Make a note of the URL of your worker (it will be something like
    ``https://drafter-gemini-proxy.your-username.workers.dev``). You will need this URL in the next step.

Configure Drafter to Use the Proxy
----------------------------------

Now that your proxy server is set up, you need to configure your Drafter site to use it for Gemini requests.

1. At the top of your Drafter file, after the import, you need to set the LLM to Gemini and specify the proxy URL.
   You should use the URL of your CloudFlare Worker that you noted in the previous step.

.. code-block:: python

    from drafter import *
    from drafter.llm import *

    set_gemini_server("https://drafter-gemini-proxy.your-username.workers.dev")


Then, subsequently, you can call the LLM as usual in your Drafter code, except you no longer need to set the API key.

.. code-block:: python

    conversation = []

    conversation.append(LLMMessage("user", "Hello, Gemini!"))

    response = call_gemini(conversation)

And theoretically, this should work! You'll get back a ``LLMResponse`` object as usual, which should have the ``content`` field
with the results of your query.

Example LLM Integration
-----------------------

Here's a complete example of how to set up a simple Drafter site that uses Gemini via the proxy server.
This is a simple chatbot application.

.. code-block:: python

    from bakery import assert_equal
    from drafter import *
    from dataclasses import dataclass
    from drafter.llm import LLMMessage, LLMResponse, call_gemini, set_gemini_server



    set_site_information(
        author="your_email@udel.edu",
        description="A brief description of what your website does",
        sources="List any help resources or sources you used",
        planning="your_planning_document.pdf",
        links=["https://github.com/your-username/your-repo"]
    )

    set_gemini_server("https://your-url-goes-here.workers.dev/")


    hide_debug_information()
    set_website_title("Your Drafter Website")
    set_website_framed(False)


    @dataclass
    class State:
        """
        The state of our chatbot application.

        :param conversation: List of messages in the conversation
        :type conversation: List[LLMMessage]
        """
        conversation: list[LLMMessage]


    @route
    def index(state: State) -> Page:
        """
        Main page of the chatbot application.
        Shows API key setup if not configured, otherwise shows the chat interface.
        """
        return show_chat(state)


    def show_chat(state: State) -> Page:
        """Display the chat interface with conversation history."""
        content = [
            f"Chatbot using Gemini",
            "---"
        ]

        # Show conversation history
        if state.conversation:
            for msg in state.conversation:
                if msg.role == "user":
                    content.append(f"You: {msg.content}")
                elif msg.role == "assistant":
                    content.append(f"Bot: {msg.content}")
            content.append("---")

        # Input for new message
        content.extend([
            "Your message:",
            TextArea("user_message", "", rows=3, cols=50),
            LineBreak(),
            Button("Send", send_message),
            Button("Clear Conversation", clear_conversation),
        ])

        return Page(state, content)


    @route
    def send_message(state: State, user_message: str) -> Page:
        """Send a message to the LLM and get a response."""
        if not user_message.strip():
            return show_chat(state)

        # Add user message to conversation
        user_msg = LLMMessage("user", user_message)
        state.conversation.append(user_msg)

        result = call_gemini(state.conversation)

        # Handle the result
        if isinstance(result, LLMResponse):
            # Success! Add the response to conversation
            assistant_msg = LLMMessage("assistant", result.content)
            state.conversation.append(assistant_msg)
        else:
            # Error occurred
            error_msg = LLMMessage("assistant", f"Error: {result.message}")
            state.conversation.append(error_msg)
        return show_chat(state)


    @route
    def clear_conversation(state: State) -> Page:
        """Clear the conversation history."""
        state.conversation = []
        return show_chat(state)


    start_server(State([]))
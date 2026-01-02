def default_index(state):
    """
    The default index page for the website. This will show a simple "Hello world!" message.
    You should not modify or use this function; instead, create your own index page.
    """
    from drafter.payloads.kinds.page import Page
    
    return Page(state, ["Hello world!", "Welcome to Drafter."])
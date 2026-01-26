def default_index(state):
    """Display the default welcome page.

    This is the built-in index route shown when no user-provided index
    exists. Users should create their own index page instead of modifying
    this function.

    Args:
        state: Current application state.

    Returns:
        Page: Simple welcome message.
    """
    from drafter.payloads.kinds.page import Page
    
    return Page(state, ["Hello world!", "Welcome to Drafter."])
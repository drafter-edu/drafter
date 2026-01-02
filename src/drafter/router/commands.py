from typing import Union, Callable, Optional, TypeVar, overload, ParamSpec, cast, List, Dict, Any
from functools import wraps
import time
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import get_main_server
from drafter.router.introspect import get_signature

T = TypeVar("T", bound=Callable[..., object])

@overload
def route(url: T) -> T: ...
@overload
def route(
    url: Union[str, None] = None, 
    server: Optional[ClientServer] = None,
    ignore_parameters: Optional[List[str]] = None,
    default_parameters: Optional[Dict[str, Any]] = None
) -> Callable[[T], T]: ...
def route(
    url: Union[str, None, T] = None,
    server: Optional[ClientServer] = None,
    ignore_parameters: Optional[List[str]] = None,
    default_parameters: Optional[Dict[str, Any]] = None,
) -> Union[T, Callable[[T], T]]:
    """
    Main function to add a new route to the server. Recommended to use as a decorator.
    Once added, the route will be available at the given URL; the function name will be used if no URL is provided.
    When you go to the URL, the function will be called and its return value will be displayed.

    :param url: The URL to add the route to. If None, the function name will be used.
    :param server: The server to add the route to. Defaults to the main server.
    :param ignore_parameters: List of parameter names to ignore when routing. These parameters
                             will be silently dropped and not cause warnings or errors.
    :param default_parameters: Dictionary of default parameter values to use when parameters
                              are not provided in the request. Example: {'page': 1, 'limit': 10}
    :return: The modified route function.
    """

    server = server or get_main_server()
    if callable(url):
        func = cast(T, url)
        local_url = func.__name__
        server.add_route(
            local_url, func, 
            ignore_parameters=ignore_parameters or [],
            default_parameters=default_parameters or {}
        )
        return func
    
    def make_route(func: T) -> T:
        local_url = url if url is not None else func.__name__
        server.add_route(
            local_url, func, 
            ignore_parameters=ignore_parameters or [],
            default_parameters=default_parameters or {}
        )
        return func

    return make_route


def timer(func: T) -> T:
    """
    Decorator that times the execution of a route handler and logs the duration.
    
    Example:
        @timer
        @route
        def slow_page(state):
            # Do some work
            return Page(state, [Text("Done")])
    
    The execution time will be logged to the console.
    
    :param func: The route handler function to time
    :return: The wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"⏱️ Route '{func.__name__}' executed in {elapsed:.4f} seconds")
        return result
    return cast(T, wrapper)


def error_handler(error_type: type[Exception]) -> Callable[[T], T]:
    """
    Decorator that registers a custom error page handler for a specific exception type.
    
    Example:
        @error_handler(ValueError)
        def handle_value_error(state, error):
            return Page(state, [
                Heading("Value Error"),
                Text(f"An error occurred: {error}")
            ])
    
    When a ValueError is raised during routing, this handler will be called
    to generate a custom error page instead of the default error screen.
    
    Note: This stores the error handler in the function's metadata for potential
    future use when the server implements error handler registration.
    
    :param error_type: The exception class to handle
    :return: Decorator function that registers the error handler
    """
    def decorator(func: T) -> T:
        # Store the error handler in the function's metadata for future use
        if not hasattr(func, '_error_handlers'):
            func._error_handlers = {}
        func._error_handlers[error_type] = func
        
        # TODO: Register with the main server once register_error_handler is implemented
        # server = get_main_server()
        # if hasattr(server, 'register_error_handler'):
        #     server.register_error_handler(error_type, func)
        
        return func
    return decorator

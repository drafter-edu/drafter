from dataclasses import dataclass
from typing import Optional, Any
from drafter.data.request import Request
from drafter.payloads.payloads import ResponsePayload
from drafter.payloads.kinds.page import Page
from drafter.components import PageContent
from drafter.payloads.failure import VerificationFailure


def verify_response_payload_type(request: Request, payload: ResponsePayload):
    """Validate that a payload is a ResponsePayload instance.

    If the payload is None, a string, list, or non-ResponsePayload type,
    returns a descriptive error message. Otherwise returns None.

    Args:
        request: Associated request providing context (URL).
        payload: Object to validate as a ResponsePayload.

    Returns:
        str or None: Error message if invalid, None if valid.
    """
    original_function = request.url
    message = None
    if payload is None:
        message = (
            f"The server did not return a Page() object from {original_function}.\n"
            f"Instead, it returned None (which happens by default when you do not return anything else).\n"
            f"Make sure you have a proper return statement for every branch!"
        )
    elif isinstance(payload, str):
        message = (
            f"The server did not return a Page() object from {original_function}. Instead, it returned a string:\n"
            f"  {payload!r}\n"
            f"Make sure you are returning a Page object with the new state and a list of strings!"
        )
    elif isinstance(payload, list):
        message = (
            f"The server did not return a Page() object from {original_function}. Instead, it returned a list:\n"
            f" {payload!r}\n"
            f"Make sure you return a Page object with the new state and the list of strings, not just the list of strings."
        )
    elif not isinstance(payload, ResponsePayload):
        message = (
            f"The server did not return a Page() object from {original_function}. Instead, it returned:\n"
            f" {payload!r}\n"
            f"Make sure you return a Page object with the new state and the list of strings."
        )

    return message


def verify_page_state_history(
    request: Request, updated_state: Any, state_history: list
) -> Optional[str]:
    """Validate state type consistency with previous state history.

    Ensures the new state object has the same type as the most recent
    state in the history. Returns an error message if types don't match.

    Args:
        request: Associated request providing context (URL).
        updated_state: New state value to verify.
        state_history: List of previous state objects.

    Returns:
        str or None: Error message if type mismatch, None if valid.
    """
    original_function = request.url
    if not state_history:
        return None  # No history to compare against
    last_type = state_history[-1].__class__
    if not isinstance(updated_state, last_type):
        return (
            f"The server did not return a valid Page() object from {original_function}. The state object's type changed from its previous type. The new value is:\n"
            f" {updated_state!r}\n"
            f"The most recent value was:\n"
            f" {state_history[-1]!r}\n"
            f"The expected type was:\n"
            f" {last_type}\n"
            f"Make sure you return the same type each time."
        )
    return None

from dataclasses import dataclass
from drafter.payloads.payloads import ResponsePayload
from drafter.payloads.kinds.page import Page
from drafter.components import PageContent
from drafter.payloads.failure import VerificationFailure


def verify_response_payload(payload: ResponsePayload):
    pass


def verify_page_result(self, page, original_function):
    """
    Verifies the result of a function execution to ensure it returns a valid `Page`
    object. The verification checks whether the returned result is of type `Page`
    and whether its structure adheres to the expected format. If the validation
    fails, an error message is generated and returned.

    :param page: The object returned by the endpoint method to be verified.
    :type page: Union[None, str, list, Any]
    :param original_function: A reference to the function or method where the
        `Page` object is expected to be returned from.
    :type original_function: Callable
    :return: Returns either a valid `Page` object or an error page with diagnostic
        information when the verification process fails.
    :rtype: Optional[Page]
    """
    message = ""
    if page is None:
        message = (
            f"The server did not return a Page object from {original_function}.\n"
            f"Instead, it returned None (which happens by default when you do not return anything else).\n"
            f"Make sure you have a proper return statement for every branch!"
        )
    elif isinstance(page, str):
        message = (
            f"The server did not return a Page() object from {original_function}. Instead, it returned a string:\n"
            f"  {page!r}\n"
            f"Make sure you are returning a Page object with the new state and a list of strings!"
        )
    elif isinstance(page, list):
        message = (
            f"The server did not return a Page() object from {original_function}. Instead, it returned a list:\n"
            f" {page!r}\n"
            f"Make sure you return a Page object with the new state and the list of strings, not just the list of strings."
        )
    elif not isinstance(page, Page):
        message = (
            f"The server did not return a Page() object from {original_function}. Instead, it returned:\n"
            f" {page!r}\n"
            f"Make sure you return a Page object with the new state and the list of strings."
        )
    else:
        verification_status = self.verify_page_state_history(page, original_function)
        if verification_status:
            return verification_status
        elif isinstance(page.content, str):
            message = (
                f"The server did not return a valid Page() object from {original_function}.\n"
                f"Instead of a list of strings or content objects, the content field was a string:\n"
                f" {page.content!r}\n"
                f"Make sure you return a Page object with the new state and the list of strings/content objects."
            )
        elif not isinstance(page.content, list):
            message = (
                f"The server did not return a valid Page() object from {original_function}.\n"
                f"Instead of a list of strings or content objects, the content field was:\n"
                f" {page.content!r}\n"
                f"Make sure you return a Page object with the new state and the list of strings/content objects."
            )
        else:
            for item in page.content:
                if not isinstance(item, (str, PageContent)):
                    message = (
                        f"The server did not return a valid Page() object from {original_function}.\n"
                        f"Instead of a list of strings or content objects, the content field was:\n"
                        f" {page.content!r}\n"
                        f"One of those items is not a string or a content object. Instead, it was:\n"
                        f" {item!r}\n"
                        f"Make sure you return a Page object with the new state and the list of strings/content objects."
                    )

    if message:
        return self.make_error_page(
            "Error after creating page", ValueError(message), original_function
        )


def verify_page_state_history(self, page, original_function):
    """
    Validates the consistency of the state object's type in the provided `page`
    against the most recent state stored in the `self._state_history`. If any
    discrepancy is found in the type of the state object, it constructs an error
    message highlighting the inconsistency and generates an error page.

    :param page: The page object containing the state to be verified.
    :param original_function: The name of the function that created the page.
    :return: Returns an error page if a validation issue arises, otherwise none.
    """
    if not self._state_history:
        return
    message = ""
    last_type = self._state_history[-1].__class__
    if not isinstance(page.state, last_type):
        message = (
            f"The server did not return a valid Page() object from {original_function}. The state object's type changed from its previous type. The new value is:\n"
            f" {page.state!r}\n"
            f"The most recent value was:\n"
            f" {self._state_history[-1]!r}\n"
            f"The expected type was:\n"
            f" {last_type}\n"
            f"Make sure you return the same type each time."
        )
    # TODO: Typecheck each field
    if message:
        return self.make_error_page(
            "Error after creating page", ValueError(message), original_function
        )

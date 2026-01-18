"""
Status codes loosely follow HTTP status code conventions.
    - 1xx: Informational (not used currently)
    - 2xx: Success
    - 3xx: Redirects (not used currently)
    - 4xx: User developer errors (i.e., in the route itself)
    - 5xx: BridgeClient errors
    - 6xx: ClientServer errors
    - 7xx: AppServer/BuildServer errors


Error if the user tries to provide a route function with untyped parameters.
Error if an error occurred during parameter conversion.
Error if a parameter was expected but not provided in the request.
Warning if the user has a route function that does not have `state` or `page` as its first parameter.
Warning if the user provided a parameter that is not used by the route function.

Let's make a list of all the possible error locations:
- During page load, not in Engine:
    - While trying to show a skulpt error, there's a further error.
- During page load, in Engine
    - During initial setup of the page,

"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ErrorKind:
    name: str
    reason: str = ""
    suggestion: str = ""
    severity: str = "error"  # could be 'error', 'warning'

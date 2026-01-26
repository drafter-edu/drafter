from dataclasses import dataclass


@dataclass
class VerificationFailure:
    """Record a payload verification failure with error message.

    Attributes:
        message: Description of the verification failure.
    """
    message: str

"""The `VerificationFailure` record produced when a payload fails verification."""

from dataclasses import dataclass


@dataclass
class VerificationFailure:
    """Record a payload verification failure with error message.

    Like `ErrorDetails`, a failure carries two tiers of text: the technically
    concise `message`, and an optional student-friendly tier
    (`friendly_title`/`friendly_message`/`friendly_steps`). Verification
    checks that build their diagnosis directly (no exception involved) should
    author the friendly tier here so the error page gets tailored guidance
    instead of generic fallback advice (which, among other things, tells
    students to read a traceback that a message-only failure never has).

    Attributes:
        message: Description of the verification failure.
        exception: The originating exception, when verification failed by
            raising (e.g. a `StudentFacingError` from `Link.verify`). Carrying
            it here lets the error envelope keep the exception's traceback and
            any student-friendly explanation it provides, instead of falling
            back to generic guidance.
        friendly_title: Short page-title-style label for the failure.
        friendly_message: Plain-language explanation for novice programmers.
        friendly_steps: Concrete "what to try next" suggestions.
    """

    message: str
    exception: Exception | None = None
    friendly_title: str = ""
    friendly_message: str = ""
    friendly_steps: tuple[str, ...] = ()

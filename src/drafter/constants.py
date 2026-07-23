"""
Constants that are used throughout the project.
"""

RESTORABLE_STATE_KEY = "--restorable-state"
"""Reserved form field name for carrying a serialized copy of the application
state, so that submitting a page can restore that state. Kept for
compatibility with Drafter v1's debug tooling; the v2 router does not
currently read it."""

SUBMIT_BUTTON_KEY = "--submit-button"
"""Form field name that records which button or submit link was pressed.
`Button` and `SubmitInput` render with this as their `name` attribute; the
bridge and router pop this key out of the submitted data to determine the
target route (and its `button_pressed` value), and the parameter pipeline
excludes it from route parameters."""

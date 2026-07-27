"""Testing helpers for Drafter sites.

Re-exports Drafter's jest-like assertion toolkit (`assert_equal`,
`assert_page`, `assert_state`, `assert_content`, the `assert_has` /
`assert_in` family, and the component-detail assertions) along with the
`set_assertion_defaults` flag control. Importing this package also
installs Drafter's test tracking into the Bakery library when it is
available, so legacy `from bakery import assert_equal` tests are still
recorded in the debug panel.
"""

# Importing drafter.testing.testing patches Bakery's assert_equal (when
# Bakery is installed) so those calls are tracked in the debug panel.
from drafter.testing import testing as _bakery_integration  # noqa: F401
from drafter.testing.asserts import (
    assert_attribute,
    assert_children,
    assert_content,
    assert_equal,
    assert_has,
    assert_has_regex,
    assert_in,
    assert_in_regex,
    assert_not_has,
    assert_not_in,
    assert_page,
    assert_state,
    assert_style,
    assert_text,
)
from drafter.testing.reporting import (
    AssertionDefaults,
    get_assertion_defaults,
    set_assertion_defaults,
)

__all__ = [
    "assert_equal",
    "assert_page",
    "assert_state",
    "assert_content",
    "assert_has",
    "assert_in",
    "assert_not_has",
    "assert_not_in",
    "assert_has_regex",
    "assert_in_regex",
    "assert_attribute",
    "assert_style",
    "assert_children",
    "assert_text",
    "AssertionDefaults",
    "get_assertion_defaults",
    "set_assertion_defaults",
]

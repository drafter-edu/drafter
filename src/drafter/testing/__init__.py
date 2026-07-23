"""Testing helpers for Drafter sites.

Re-exports `assert_equal`, the (Bakery-instrumented) assertion students
use in their tests; importing it also installs Drafter's test tracking
into Bakery when that library is available.
"""

from drafter.testing.testing import assert_equal

__all__ = [
    "assert_equal",
]

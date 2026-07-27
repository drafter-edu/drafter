from bakery import assert_equal

from drafter import *


@route("index")
def index():
    return Page(None, ["Hello, World!"])


assert_equal(index(), Page(None, ["Hello, World!"]))

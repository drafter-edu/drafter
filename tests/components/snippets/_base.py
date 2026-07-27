from collections import defaultdict


class TestableComponentSet:
    def __init__(self, name):
        self._name = name
        self._tests = defaultdict(list)

    def __setattr__(self, key, value):
        if key in ("_tests", "_name"):
            super().__setattr__(key, value)
        else:
            self._tests[key].append(value)

    def get_tests(self):
        return self._tests

from drafter.setup import *
from drafter.components import *
from drafter.styling import *
from drafter.routes import *
from drafter.server import *
from drafter.deploy import *
from drafter.testing import assert_equal

# Provide default route
route('index')(default_index)

__version__ = '1.2.0'

if __name__ == '__main__':
    print("This package is meant to be imported, not run as a script. For now, at least.")

"""
This is the main entry point for Drafter when you run it as a module:

```
python -m drafter
```

The sys.argv will be something like:
```
['../drafter/__main__.py', 'my_site.py', '--some-flag']
```

Instead, you probably want to run either your program or the
Drafter CLI directly, e.g.:

```
python my_site.py
# or
drafter my_site.py
```

"""


import sys
from drafter.cli import main

if __name__ == "__main__":
    main()
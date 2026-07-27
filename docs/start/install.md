---
page_type: how-to
title: Get Drafter running
level: L1
audience: S
priority: P0
prereqs: []
symbols: []
outcome: Get Drafter installed and verified locally.
---

# Get Drafter running

## Goal

You want Drafter installed on your computer and proof that it works, so you
can start building.

## Before you start

You need Python 3.10 or newer installed, and an editor you can run Python
files from. The steps below cover [Thonny](https://thonny.org/) (common in
introductory courses) and the command line. Any editor works: Drafter is an
ordinary Python package, so install it however you normally install
packages.

## Install

Thonny has a built-in package manager:

1. Open **Tools**, then **Manage packages**.
2. Type `drafter` in the search bar and press **Find packages from PyPI**.
3. Select **drafter** in the results and press **Install**.


!!! note "Note"
    If the package manager is unavailable, open **Tools**, then
    **Open system shell**, and type:

    ```text
    pip install drafter
    ```

    If you aren't using Thonny, then in a terminal (Command Prompt, PowerShell, or a shell):

    ```text
    pip install drafter
    ```

    If you use virtual environments, activate yours first and install into it.

## Verify it worked

Create a new Python file, put this single line in it, and run it:

```python
from drafter import *
```

If it runs without an error, Drafter is installed. Nothing visible happens
yet; that is expected. Your first page is one step away.

## Common problems

- **`No module named 'drafter'`**: the install went to a different Python
  than the one running your file. In Thonny, install through
  **Tools → Manage packages** so the right Python is used. On the command
  line, try `python -m pip install drafter` so pip and Python match.
- **`pip` is not recognized**: use `python -m pip install drafter`
  instead, or on some systems `py -m pip install drafter`.
- **Permission errors on shared or lab machines**: try
  `pip install --user drafter`, or ask your instructor how packages are
  managed on lab computers.
- **It installed, but an old version**: upgrade with
  `pip install --upgrade drafter`.

Still stuck? See [Troubleshooting](../help/troubleshooting.md).

<div class="grid cards" markdown>

- **Next: Build your first app**

    ---

    A working counter site, built one idea at a time, in about twenty
    minutes.

    [Build your first app](first-app.md)

</div>

# If we can find a start_server line, that's easiest
# If not, then we can look up the stack for the first file that isn't part of Drafter itself,
#    but need to dodge other launching systems like Thonny, pytest, or the Starlette reloader.
#

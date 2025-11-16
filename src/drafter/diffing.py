import difflib

DIFF_INDENT_WIDTH = 1
DIFF_WRAP_WIDTH = 60
differ = difflib.HtmlDiff(tabsize=DIFF_INDENT_WIDTH, wrapcolumn=DIFF_WRAP_WIDTH)


def change_diff_settings(indent_width=1, wrap_width=60):
    """Change the settings for the diff output."""
    global differ, DIFF_WRAP_WIDTH
    differ = difflib.HtmlDiff(tabsize=indent_width, wrapcolumn=wrap_width)
    DIFF_WRAP_WIDTH = wrap_width


def get_indent_width():
    """Get the current indent width for diffs."""
    return DIFF_INDENT_WIDTH


def diff_tests(left, right, left_name, right_name):
    """Compare two strings and show the differences in a table."""
    try:
        table = differ.make_table(
            left.splitlines(), right.splitlines(), left_name, right_name
        )
        return table
    except:
        if left == right:
            return "No differences found."
        return f"<pre>{left}</pre><pre>{right}</pre>"

import difflib

DIFF_INDENT_WIDTH = 1
DIFF_WRAP_WIDTH = 60
differ = difflib.HtmlDiff(tabsize=DIFF_INDENT_WIDTH, wrapcolumn=DIFF_WRAP_WIDTH)


def change_diff_settings(indent_width=1, wrap_width=60):
    """Change diff table formatting settings.

    Args:
        indent_width: Number of spaces to use for tab expansion.
        wrap_width: Column width for wrapping diff output.
    """
    global differ, DIFF_WRAP_WIDTH
    differ = difflib.HtmlDiff(tabsize=indent_width, wrapcolumn=wrap_width)
    DIFF_WRAP_WIDTH = wrap_width


def get_indent_width():
    """Return the current indent width for diffs.

    Returns:
        int: Tab size used by the diff generator.
    """
    return DIFF_INDENT_WIDTH


def diff_tests(left, right, left_name, right_name):
    """Generate an HTML table showing differences between two strings.

    Args:
        left: Baseline string content.
        right: Target string content to compare.
        left_name: Label for the baseline column.
        right_name: Label for the target column.

    Returns:
        str: HTML table representing the differences.

    Raises:
        Exception: Propagates exceptions from the underlying diff generator.
    """
    try:
        table = differ.make_table(
            left.splitlines(), right.splitlines(), left_name, right_name
        )
        return table
    except Exception as e:
        raise e
        if left == right:
            return "No differences found."
        return f"<pre>{left}</pre><pre>{right}</pre>"

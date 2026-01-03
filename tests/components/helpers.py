import linecache
import uuid
import drafter

def eval_drafter_with_source(
    snippet: str,
    category: str,
    name: str,
    *,
    globals=None,
    locals=None,
    filename: str | None = None,
):
    """
    Evaluate a Python expression while preserving source code
    in tracebacks.

    Parameters
    ----------
    snippet : str
        The expression to evaluate.
    globals, locals : dict | None
        Execution context.
    filename : str | None
        Optional virtual filename for tracebacks.
        If omitted, a unique one is generated.

    Returns
    -------
    Any
        Result of evaluating the expression.
    """
    if filename is None:
        filename = f"<eval-snippet-{uuid.uuid4()}>"

    # Ensure linecache knows about this "file"
    lines = snippet.splitlines(keepends=True)
    linecache.cache[filename] = (
        len(snippet),
        None,
        lines,
        filename,
    )
    
    drafter_eval_globals = {
        "__builtins__": __builtins__,
        **vars(drafter),
    }
    if globals is not None:
        drafter_eval_globals.update(globals)

    try:
        code = compile(snippet, filename, "eval")
        return eval(code, drafter_eval_globals, locals)
    except Exception as e:
        raise AssertionError(
            f"{category} / {name}: evaluating the repr() of the object raised an exception:\n\n"
            f"Snippet:\n{snippet}\n\nException:\n{e}"
        ) from e
    finally:
        # Optional cleanup: remove cached source to avoid growth
        linecache.cache.pop(filename, None)
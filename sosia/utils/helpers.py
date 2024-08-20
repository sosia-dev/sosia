"""Module with helper functions."""

def custom_print(text, verbose):
    """Print text if verbose."""
    if verbose:
        print(text)


def run(op, *args):
    """Call a function passed by partial()."""
    return op(*args)


def _get_obj_name(obj):
    """Auxiliary function to retrieve the name of an object."""
    name = str(obj).replace("class ", "")
    return name.translate(str.maketrans({c: "" for c in "(<>),'"}))

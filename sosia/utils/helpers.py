def custom_print(text, verbose):
    """Print text if verbose."""
    if verbose:
        print(text)


def print_progress(iteration, total, verbose=True, length=50):
    """Print terminal progress bar."""
    if not verbose:
        return None
    share = iteration / float(total)
    filled_len = int(length * iteration // total)
    bar = "█" * filled_len + "-" * (length - filled_len)
    print(f"\rProgress: |{bar}| {share:.2%} complete", end="\r")
    if iteration == total:
        print()


def run(op, *args):
    """Call a function passed by partial()."""
    return op(*args)


def _get_obj_name(obj):
    """Auxiliary function to retrieve the name of an object."""
    name = str(obj).replace("class ", "")
    return name.translate(str.maketrans({c: "" for c in "(<>),'"}))

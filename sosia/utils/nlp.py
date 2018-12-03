def clean_abstract(s):
    """Clean an abstract of a document."""
    # Remove copyright statement, which can be leading or trailing
    tokens = s.split(". ")
    if "©" in tokens[0]:
        return ". ".join(tokens[1:])
    for idx in (-2, -1):
        if "©" in tokens[idx]:
            return ". ".join(tokens[:idx]) + "."
    else:
        return s


def compute_cosine(matrix, digits=4):
    """Compute cosine given a regular matrix."""
    return (matrix * matrix.T).toarray().round(digits)[-1]

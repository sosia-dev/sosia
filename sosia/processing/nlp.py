def compute_cosine(matrix, digits=4):
    """Compute cosine given a regular matrix."""
    return (matrix * matrix.T).toarray().round(digits)[-1][0]


def compute_similarity(left, right, tokenize=False, **kwds):
    """Compute cosine similarity from tfidf-weighted matrix consisting
    of two vectors (left and right).
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    if not left and not right:
        return None
    vec = TfidfVectorizer(**kwds)
    return compute_cosine(vec.fit_transform([left, right]))

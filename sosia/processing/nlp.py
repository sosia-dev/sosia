def clean_abstract(s):
    """Clean an abstract of a document."""
    # Remove copyright statement, which can be leading or trailing
    tokens = s.split(". ")
    if "©" in tokens[0]:
        return ". ".join(tokens[1:])
    for idx in (-2, -1):
        try:
            if "©" in tokens[idx]:
                return ". ".join(tokens[:idx]) + "."
        except:
            pass
    else:
        return s


def compute_cosine(matrix, digits=4):
    """Compute cosine given a regular matrix."""
    return (matrix * matrix.T).toarray().round(digits)[-1][0]


def compute_similarity(left, right, tokenize=False, **kwds):
    """Compute cosine similarity from tfidf-weighted matrix consisting
    of two vectors (left and right).
    """
    if not left and not right:
        return None
    from sklearn.feature_extraction.text import TfidfVectorizer
    if tokenize:
        kwds.update({"tokenizer": tokenize_and_stem})
    vec = TfidfVectorizer(**kwds)
    return compute_cosine(vec.fit_transform([left, right]))


def tokenize_and_stem(text):
    """Auxiliary function to return stemmed tokens of document."""
    from nltk import snowball, word_tokenize
    return [snowball.SnowballStemmer("english").stem(t) for
            t in word_tokenize(text.lower())]

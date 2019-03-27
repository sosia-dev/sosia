from nltk import snowball, word_tokenize


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


def compute_cos(matrix, digits=4):
    """Compute cosine given a regular matrix."""
    return (matrix * matrix.T).toarray().round(digits)[-1][0]


def tokenize_and_stem(text):
    """Auxiliary function to return stemmed tokens of document"""
    return [snowball.SnowballStemmer("english").stem(t) for
            t in word_tokenize(text.lower())]

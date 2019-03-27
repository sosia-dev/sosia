from nltk import snowball, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer


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


def tfidf_cos(corpus, stop_words=None, tokenize=False, **kwds):
    """Compute cosine similiarity after tfidf transformation between
    any string in `corpus` and the last string in `corpus`.

    Parameters
    ----------
    corpus : list of str
        The documents that should be vectorized and computed.

    stop_words : list (optional, default=None)
        A list of words to remove from each string in `corpus`.

    tokenize : bool (optional, default=False)
        Whether to tokenize the text and stem the words, or not.
        nltk's SnowballStemmer will be used.

    kwds : key-value pairs
        Parameters to be passed on to the TfidfVectorizer (only applies of
        `tokenize=True`)

    Returns
    -------
    cos : list
        A list of cosine similiarities between each document and the last
        document.
    """
    if not tokenize:
        vec = TfidfVectorizer(**kwds)
    else:
        vec = TfidfVectorizer(stop_words=stop_words,
                              tokenizer=tokenize_and_stem, **kwds)
    cos = []
    for i in range(0, len(corpus) - 1):
        try:
            cos.append(compute_cos(vec.fit_transform([corpus[i], corpus[-1]])))
        except AttributeError:
            cos.append(None)
    return cos


def tokenize_and_stem(text):
    """Auxiliary function to return stemmed tokens of document"""
    return [snowball.SnowballStemmer("english").stem(t) for
            t in word_tokenize(text.lower())]

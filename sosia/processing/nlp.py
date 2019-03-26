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


def tfidf_cos(docs, stop_words=None, tokenize=False, **kwds):
    """Compute cosine similiarity after tfidf transformation between
    any string (composing test) in `docs` with the last string in `docs`.
    """
    if not tokenize:
        vec = TfidfVectorizer(**kwds)
    else:
        vec = TfidfVectorizer(stop_words=stop_words,
                              tokenizer=tokenize_and_stem, **kwds)
    cos = []
    for i in range(0, len(docs) - 1):
        try:
            cos.append(compute_cos(vec.fit_transform([docs[i], docs[-1]])))
        except AttributeError:
            cos.append(None)
    return cos


def tokenize_and_stem(text):
    """Auxiliary function to return stemmed tokens of document"""
    return [snowball.SnowballStemmer("english").stem(t) for
            t in word_tokenize(text.lower())]

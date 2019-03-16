from collections import namedtuple
from operator import attrgetter

from scopus import AbstractRetrieval
from scopus.exception import Scopus404Error

from sosia.processing.nlp import clean_abstract, tfidf_cos


def find_country(auth_ids, pubs, year, refresh):
    """Find the most common country of affiliations of a scientist using her
    most recent publications listing valid affiliations.

    Parameters
    ----------
    auth_ids : list of str
        A list of Scopus Author Profile IDs for which the affiliation should
        be searched for.

    pubs : list of namedtuple
        The publications associated with the Author IDs as returned from a
        scopus query.

    year : int
        The year for which we would like to have the country.

    refresh : bool
        Whether to refresh all cached files or not.

    Returns
    -------
    country : str or None
        The country of the scientist in the year closest to the given year,
        given that the publications list valid affiliations.  Equals None when
        no valid publications are found.
    """
    # Available papers of most recent year with publications
    papers = [p for p in pubs if int(p.coverDate[:4]) <= year]
    papers = sorted(papers, key=attrgetter("coverDate"), reverse=True)
    params = {"view": "FULL", "refresh": refresh}
    for p in papers:
        authorgroup = AbstractRetrieval(p.eid, **params).authorgroup or []
        countries = [a.country for a in authorgroup if a.auid in auth_ids and a.country]
        if not countries:
            continue
        return "; ".join(sorted(list(set(countries))))


def get_authors(pubs):
    """Get list of author IDs from a list of namedtuples representing
    publications.
    """
    l = [x.author_ids.split(";") for x in pubs if isinstance(x.author_ids, str)]
    return [au for sl in l for au in sl]


def get_auth_from_df(pubs):
    """Get list of author IDs from a dataframe of publications.
    """
    l = [x.split(";") for x in pubs.author_ids if isinstance(x, str)]
    return [au for sl in l for au in sl]


def inform_matches(profiles, focal, stop_words, verbose, refresh, **kwds):
    """Create namedtuple adding information to matches.

    Parameters
    ----------
    profiles : list of Scientist
        A list of Scientist objects representing matches.

    focal : Scientist
        Object of class Scientist representing the focal scientist.

    stop_words : list
        A list of words that should be filtered in the analysis of abstracts.

    verbose : bool
        Whether to report on the progress of the process and the completeness
        of document information.

    refresh : bool
        Whether to refresh all cached files or not.

    kwds : keywords
        Parameters to pass to TfidfVectorizer for abstract vectorization.

    Returns
    -------
    m : list of namedtuples
        A list of namedtuples representing matches.  Provided information
        are "ID name first_year num_coauthors num_publications country
        language reference_sim abstract_sim".
    """
    # Add characteristics
    ids = [p.identifier[0] for p in profiles]
    names = [p.name for p in profiles]
    first_years = [p.first_year for p in profiles]
    n_coauths = [len(p.coauthors) for p in profiles]
    n_pubs = [len(p.publications) for p in profiles]
    countries = [p.country for p in profiles]
    languages = [p.get_publication_languages().language for p in profiles]
    # Add content analysis
    pubs = [[d.eid for d in p.publications] for p in profiles]
    pubs.append([d.eid for d in focal.publications])
    tokens = [parse_doc(pub, refresh) for pub in pubs]
    ref_cos = tfidf_cos([d["refs"] for d in tokens], **kwds)
    abs_cos = tfidf_cos(
        [d["abstracts"] for d in tokens], tokenize=True, stop_words=stop_words, **kwds
    )
    if verbose:
        for auth_id, d in zip(ids, tokens):
            _print_missing_docs(auth_id, d)
        label = ";".join(focal.identifier) + " (focal)"
        _print_missing_docs(label, tokens[-1])  # focal researcher
    # Merge information into list of namedtuple
    t = zip(
        ids,
        names,
        first_years,
        n_coauths,
        n_pubs,
        countries,
        languages,
        ref_cos,
        abs_cos,
    )
    fields = (
        "ID name first_year num_coauthors num_publications country "
        "language reference_sim abstract_sim"
    )
    match = namedtuple("Match", fields)
    return [match(*tup) for tup in list(t)]


def parse_doc(eids, refresh):
    """Find abstract and references of articles published up until
    the given year, both as continuous string.

    Parameters
    ----------
    eids : list of str
        Scopus Document EIDs representing documents to be considered.

    refresh : bool
        Whether to refresh the cached files if they exist, or not.

    Returns
    -------
    d : dict
        A dictionary with two keys: "refs" and "abstracts".  d['refs']
        includes the continuous string of Scopus Abstract EIDs representing
        cited references, joined on a blank.  d['abstracts'] includes
        the continuous string of cleaned abstracts, joined on a blank.
    """
    docs = []
    for eid in eids:
        try:
            docs.append(AbstractRetrieval(eid, view="FULL", refresh=refresh))
        except Scopus404Error:
            docs.append(None)
    # Filter None's
    absts = [clean_abstract(ab.abstract) for ab in docs if ab.abstract]
    refs = [ab.references for ab in docs if ab.references]
    return {
        "refs": " ".join([ref.id for sl in refs for ref in sl]) or None,
        "abstracts": " ".join(absts) or None,
        "total": len(eids),
        "miss_abs": len(eids) - len(absts),
        "miss_refs": len(eids) - len(refs),
    }


def _print_missing_docs(auth_id, info):
    """Auxiliary function to print information on missing abstracts and
    reference lists stored in a dictionary d.
    """
    print(
        "Researcher {}: {} abstract(s) and {} reference list(s) out of "
        "{} documents missing".format(
            auth_id, info["miss_abs"], info["miss_refs"], info["total"]
        )
    )

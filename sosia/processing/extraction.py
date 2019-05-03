from collections import namedtuple
from operator import attrgetter

from scopus import AbstractRetrieval
from scopus.exception import Scopus404Error
from sklearn.feature_extraction.text import TfidfVectorizer

from sosia.processing.nlp import clean_abstract, compute_cos, tokenize_and_stem
from sosia.utils import print_progress


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
        try:
            authorgroup = AbstractRetrieval(p.eid, **params).authorgroup or []
            countries = [a.country for a in authorgroup if a.auid in auth_ids and a.country]
            if not countries:
                continue
            return "; ".join(sorted(list(set(countries))))
        except (KeyError, AttributeError):
            continue


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
    profiles : list of Scientist()
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
    total = len(profiles)
    print_progress(0, total, verbose)
    focal_eids = [d.eid for d in focal.publications]
    focal_refs, focal_refs_n, focal_abs, focal_abs_n = parse_docs(focal_eids, refresh)
    focal_pubs_n = len(focal.publications)
    fields = "ID name first_year num_coauthors num_publications country "\
             "language reference_sim abstract_sim"
    m = namedtuple("Match", fields)
    out = []
    info = {}  # to collect information on missing information
    for idx, p in enumerate(profiles):
        # Perform content analysis
        eids = [d.eid for d in p.publications]
        refs, refs_n, absts, absts_n = parse_docs(eids, refresh)
        vec = TfidfVectorizer(**kwds)
        ref_cos = compute_cos(vec.fit_transform([refs, focal_refs]))
        vec = TfidfVectorizer(stop_words=stop_words,
                              tokenizer=tokenize_and_stem, **kwds)
        abs_cos = compute_cos(vec.fit_transform([absts, focal_abs]))
        # Save info
        meta = namedtuple("Meta", "refs absts total")
        meta(refs=refs_n, absts=absts_n, total=len(eids))
        key = "; ".join(p.identifier)
        info[key] = meta(refs=refs_n, absts=absts_n, total=len(eids))
        # Add characteristics
        new = m(ID=p.identifier[0],
                name=p.name,
                first_year=p.first_year,
                num_coauthors=len(p.coauthors),
                num_publications=len(p.publications),
                country=p.country,
                language=p.get_publication_languages().language,
                reference_sim=ref_cos,
                abstract_sim=abs_cos)
        # Finalize
        out.append(new)
        print_progress(idx+1, total, verbose)
    # Print information on missing information
    if verbose:
        for auth_id, info in info.items():
            _print_missing_docs(auth_id, info.refs, info.absts, info.total)
        label = ";".join(focal.identifier) + " (focal)"
        _print_missing_docs(label, focal_refs_n, focal_abs_n, focal_pubs_n)
    return out


def parse_docs(eids, refresh):
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
    t : tuple
        A tuple with our elements: The first element is a continuous string
        of cleaned abstracts, joined on a blank.  The second element is the
        number of documents with valid reference information.  The third
        element is a continuous string of Scopus Abstract EIDs representing
        cited references, joined on a blank.  The fourth element is the
        number of valid abstract information.
    """
    docs = []
    for eid in eids:
        try:
            docs.append(AbstractRetrieval(eid, view="FULL", refresh=refresh))
        except Scopus404Error:
            docs.append(None)
    refs = [ab.references for ab in docs if ab.references]
    valid_refs = len(refs)
    absts = [clean_abstract(ab.abstract) for ab in docs if ab.abstract]
    valid_absts = len(absts)
    return (" ".join([ref.id for sl in refs for ref in sl]) or None, valid_refs,
            " ".join(absts) or None, valid_absts)


def _print_missing_docs(auth_id, valid_abs, valid_refs, total, verbose=True):
    """Auxiliary function to print information on missing abstracts and
    reference lists stored in a dictionary d.
    """
    miss_abs = total-valid_abs
    miss_refs = total-valid_refs
    print("Researcher {}: {} abstract(s) and {} reference list(s) out of "
          "{} documents missing".format(auth_id, miss_abs, miss_refs, total))

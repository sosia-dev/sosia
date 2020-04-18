from collections import namedtuple

from pybliometrics.scopus import AbstractRetrieval
from pybliometrics.scopus.exception import Scopus404Error

from sosia.processing.nlp import clean_abstract, compute_similarity
from sosia.utils import print_progress


def find_location(auth_ids, pubs, year, refresh):
    """Find the most common country, affiliation ID, and affiliation name
    of a scientist using her most recent publications with valid information.

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
    country, affiliation_id, organization : str or None
        The country, city, affiliation ID, and affiliation name of the
        scientist in the year closest to the given year, given that the
        publications list valid information for each output. Equals None when
        no valid publications are found.
    """
    from operator import attrgetter
    # Available papers of most recent year with publications
    papers = [p for p in pubs if int(p.coverDate[:4]) <= year]
    papers = sorted(papers, key=attrgetter("coverDate"), reverse=True)
    params = {"view": "FULL", "refresh": refresh}
    # Return most recent complete information
    for p in papers:
        try:
            authgroup = AbstractRetrieval(p.eid, **params).authorgroup or []
        except Scopus404Error:
            continue
        authgroup = [a for a in authgroup if a.auid in auth_ids
                     and a.country and a.affiliation_id and a.organization]
        countries = "; ".join(sorted(set([a.country for a in authgroup])))
        aff_ids = "; ".join(sorted(set([a.affiliation_id for a in authgroup])))
        orgs = "; ".join(sorted(set([a.organization for a in authgroup])))
        if not countries and not aff_ids and not orgs:
            continue
        return (countries, aff_ids, orgs)
    # Return None-triple if all else fails
    return (countries, aff_ids, orgs)


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


def get_main_field(fields):
    """Get main 4-digit ASJC field (code) and main 2-digit ASJC field (name).


    Parameters
    ----------
    fields : iterable of int
        Lists of fields the researcher is active in.

    Returns
    -------
    t : tuple
        A 2-element tuple where the first element is the most common 4-digit
        ASJC field and the second element the short name of the most common
        2-digit ASJC field.

    Note
    ----
    We exclude multidisciplinary and give preference to non-general fields.
    """
    from collections import Counter

    from sosia.processing.constants import ASJC_2D

    # 4 digit field
    c = Counter(fields)
    try:
        c.pop(1000)  # Exclude Multidisciplinary
    except KeyError:
        pass
    top_fields = [f for f, val in c.items() if val == max(c.values())]
    if len(top_fields) == 1:
        main_4 = top_fields[0]
    else:
        non_general_fields = [f for f in top_fields if f % 1000 != 0]
        if non_general_fields:
            main_4 = non_general_fields[0]
        else:
            main_4 = top_fields[0]

    # 2 digit field
    c = Counter([str(f)[:2] for f in fields])
    try:
        c.pop(10)  # Exclude Multidisciplinary
    except KeyError:
        pass
    main_2 = int(c.most_common(1)[0][0])

    return (main_4, ASJC_2D[main_2])


def inform_matches(profiles, focal, keywords, stop_words, verbose,
                   refresh, **kwds):
    """Create namedtuple adding information to matches.

    Parameters
    ----------
    profiles : list of Scientist()
        A list of Scientist objects representing matches.

    focal : Scientist
        Object of class Scientist representing the focal scientist.

    keywords : iterable of strings
        Which information to add to matches.

    stop_words : list
        A list of words that should be filtered in the analysis of abstracts.

    verbose : bool
        Whether to report on the progress of the process and the completeness
        of document information.

    refresh : bool
        Whether to refresh all cached files or not.

    kwds : keywords
        Parameters to pass to sklearn.feature_extraction.text.TfidfVectorizer
        for abstract and reference vectorization.

    Returns
    -------
    m : list of namedtuples
        A list of namedtuples representing matches.  Provided information
        depend on provided keywords.
    """
    from sosia.classes import Scientist
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    from string import digits, punctuation
    # Create Match object
    fields = "ID name " + " ".join(keywords)
    m = namedtuple("Match", fields)
    # Preparation
    doc_parse = "reference_sim" in keywords or "abstract_sim" in keywords
    total = len(profiles)
    print_progress(0, total, verbose)
    if doc_parse:
        focal_eids = [d.eid for d in focal.publications]
        focal_docs = parse_docs(focal_eids, refresh)
        focal_refs, focal_refs_n, focal_abs, focal_abs_n = focal_docs
        stop_words = list(ENGLISH_STOP_WORDS)
        stop_words.extend(punctuation + digits)
    # Add selective information
    out = []
    info = {}  # to collect information on missing information
    for idx, p in enumerate(profiles):
        # Add characteristics
        match_info = {"ID": p.identifier[0], "name": p.name}
        if "language" in keywords:
            try:
                match_info["language"] = p.get_publication_languages().language
            except Scopus404Error:  # Refresh profile
                p = Scientist(p.identifier, p.year, refresh=True)
                match_info["language"] = p.get_publication_languages().language
        if "first_name" in keywords:
            match_info["first_name"] = p.first_name
        if "surname" in keywords:
            match_info["surname"] = p.surname
        if "first_year" in keywords:
            match_info["first_year"] = p.first_year
        if "num_coauthors" in keywords:
            match_info["num_coauthors"] = len(p.coauthors)
        if "num_publications" in keywords:
            match_info["num_publications"] = len(p.publications)
        if "num_citations" in keywords:
            match_info["num_citations"] = p.citations
        if "num_coauthors_period" in keywords:
            match_info["num_coauthors_period"] = len(p.coauthors_period)
        if "num_publications_period" in keywords:
            match_info["num_publications_period"] = len(p.publications_period)
        if "num_citations_period" in keywords:
            match_info["num_citations_period"] = p.citations_period
        if "subjects" in keywords:
            match_info["subjects"] = p.subjects
        if "country" in keywords:
            match_info["country"] = p.country
        if "city" in keywords:
            match_info["city"] = p.city
        if "affiliation_id" in keywords:
            match_info["affiliation_id"] = p.affiliation_id
        if "affiliation" in keywords:
            match_info["affiliation"] = p.organization
        # Abstract and reference similiarity is performed jointly
        if doc_parse:
            eids = [d.eid for d in p.publications]
            refs, refs_n, absts, absts_n = parse_docs(eids, refresh)
            ref_cos = compute_similarity(refs, focal_refs, **kwds)
            kwds.update({"stop_words": stop_words})
            abs_cos = compute_similarity(absts, focal_abs, tokenize=True, **kwds)
            # Save info for below print statement
            meta = namedtuple("Meta", "refs absts total")
            meta(refs=refs_n, absts=absts_n, total=len(eids))
            key = "; ".join(p.identifier)
            info[key] = meta(refs=refs_n, absts=absts_n, total=len(eids))
        if "reference_sim" in keywords:
            match_info["reference_sim"] = ref_cos
        if "abstract_sim" in keywords:
            match_info["abstract_sim"] = abs_cos
        # Finalize
        out.append(m(**match_info))
        print_progress(idx+1, total, verbose)
    # Print information on missing information
    if verbose and doc_parse:
        for auth_id, info in info.items():
            _print_missing_docs([auth_id], info.absts, info.refs, info.total)
        focal_pubs_n = len(focal.publications)
        _print_missing_docs(focal.identifier, focal_abs_n, focal_refs_n,
                            focal_pubs_n, res_type="Original")
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
            continue
    ref_lst = [ab.references for ab in docs if ab.references]
    valid_refs = len(ref_lst)
    ref_ids = [ref.id for sl in ref_lst for ref in sl]
    refs = " ".join(filter(None, ref_ids)).strip()
    absts = [clean_abstract(ab.abstract) for ab in docs if ab.abstract]
    valid_absts = len(absts)
    absts = " ".join(absts).strip()
    return (refs, valid_refs, absts, valid_absts)


def _print_missing_docs(auth_id, valid_abs, valid_refs, total, res_type="Match"):
    """Auxiliary function to print information on missing abstracts and
    reference lists stored in a dictionary d.
    """
    text = f"{res_type} {';'.join(auth_id)}: {total-valid_abs} abstract(s) "\
           f"and {total-valid_refs} reference list(s) out of {total} documents missing"
    print(text)
from collections import namedtuple

from pybliometrics.scopus import AbstractRetrieval
from pybliometrics.scopus.exception import Scopus404Error

from sosia.processing.nlp import clean_abstract, compute_similarity
from sosia.utils import print_progress


def extract_authors(pubs):
    """Get list of author IDs from a list of namedtuples representing
    publications.
    """
    l = [x.author_ids.split(";") for x in pubs if isinstance(x.author_ids, str)]
    return [au for sl in l for au in sl]


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
        scientist in the year closest to the treatment year, given that the
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
        return countries, aff_ids, orgs
    # Return None-triple if all else fails
    return countries, aff_ids, orgs


def get_main_field(fields):
    """Get main 4-digit ASJC field (code) and main 2-digit ASJC field (name).

    Parameters
    ----------
    fields : iterable of int
        Lists of fields the researcher is active in.

    Returns
    -------
    main : int
        The most common 4-digit ASJC field.

    name : str
        The name of the most common 2-digit ASJC field.

    Note
    ----
    We exclude multidisciplinary and give preference to non-general fields.
    """
    from collections import Counter

    from sosia.processing.constants import ASJC_2D

    # Exclude Multidisciplinary
    while 1000 in fields:
        fields.remove(1000)

    # Verify at least some information is present
    if not fields:
        return None, None

    # 4 digit field
    c = Counter(fields)
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
    main_2 = int(c.most_common(1)[0][0])
    name = ASJC_2D[main_2]

    return main_4, name


def inform_match(profile, keywords):
    """Create namedtuple adding information to matches.

    Parameters
    ----------
    profile : sosia.Scientist()
        A Scientist() object representing a match.

    keywords : iterable of strings
        Which information to add to the match.

    Returns
    -------
    match_info : dict
        Information corresponding to provided keywords.
    """
    from sosia.classes import Scientist

    info = {
        "ID": profile.identifier[0],
        "name": profile.name,
        "first_name": profile.first_name,
        "surname": profile.surname,
        "first_year": profile.first_year,
        "num_coauthors": len(profile.coauthors),
        "num_publications": len(profile.publications),
        "num_citations": profile.citations,
        "num_coauthors_period": len(profile.coauthors_period or "") or None,
        "num_publications_period": len(profile.publications_period or "") or None,
        "num_citations_period": profile.citations_period,
        "subjects": profile.subjects,
        "country": profile.country,
        "affiliation_id": profile.affiliation_id,
        "affiliation": profile.organization
    }
    match_info = {k: v for k, v in info.items() if k in keywords + ["ID", "name"]}
    if "language" in keywords:
        try:
            match_info["language"] = profile.get_publication_languages().language
        except Scopus404Error:  # Refresh profile
            profile = Scientist(profile.identifier, profile.year, refresh=True)
            match_info["language"] = profile.get_publication_languages().language
    return match_info


def inform_matches(self, keywords, stop_words, verbose, refresh, **kwds):
    """Add match-specific information to all matches.

    Parameters
    ----------
    self : sosia.Original()
        Object whose matches should received additional information

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
    out : list of namedtuples
        A list of namedtuples representing matches.  Provided information
        depend on provided keywords.
    """
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    from string import digits, punctuation

    from sosia.classes import Scientist

    # Create Match object
    fields = "ID name " + " ".join(keywords)
    m = namedtuple("Match", fields)

    # Preparation
    doc_parse = "reference_sim" in keywords or "abstract_sim" in keywords
    if doc_parse:
        focal_docs = parse_docs([d.eid for d in self.publications], refresh)
        focal_refs, focal_refs_n, focal_abs, focal_abs_n = focal_docs
        if not stop_words:
            stop_words = list(ENGLISH_STOP_WORDS) + list(punctuation + digits)

    # Add selected information match-by-match
    out = []
    completeness = {}
    total = len(self.matches)
    print_progress(0, total, verbose)
    meta = namedtuple("Meta", "refs absts total")
    for idx, auth_id in enumerate(self.matches):
        period = self.year + 1 - self._period_year
        p = Scientist([auth_id], self.year, period=period, refresh=refresh,
                      sql_fname=self.sql_fname)
        match_info = inform_match(p, keywords)
        # Abstract and reference similarity is performed jointly
        if doc_parse:
            eids = [d.eid for d in p.publications]
            refs, refs_n, absts, absts_n = parse_docs(eids, refresh)
            completeness[auth_id] = meta(refs=refs_n, absts=absts_n,
                                         total=len(eids))
            if "reference_sim" in keywords:
                ref_cos = compute_similarity(refs, focal_refs, **kwds)
                match_info["reference_sim"] = ref_cos
            if "abstract_sim" in keywords:
                kwds.update({"stop_words": stop_words})
                abs_cos = compute_similarity(absts, focal_abs, tokenize=True,
                                             **kwds)
                match_info["abstract_sim"] = abs_cos
        out.append(m(**match_info))
        print_progress(idx+1, total, verbose)

    # Eventually print information on missing information
    if verbose and doc_parse:
        for auth_id, completeness in completeness.items():
            _print_missing_docs([auth_id], completeness.absts,
                                completeness.refs, completeness.total)
        focal_pubs_n = len(self.publications)
        _print_missing_docs(self.identifier, focal_abs_n, focal_refs_n,
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
    return refs, valid_refs, absts, valid_absts


def _print_missing_docs(auth_id, valid_abs, valid_refs, total, res_type="Match"):
    """Auxiliary function to print information on missing abstracts and
    reference lists stored in a dictionary d.
    """
    text = f"{res_type} {';'.join(auth_id)}: {total-valid_abs} abstract(s) "\
           f"and {total-valid_refs} reference list(s) out of {total} documents missing"
    print(text)

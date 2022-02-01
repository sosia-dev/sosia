from collections import namedtuple

from pybliometrics.scopus import AbstractRetrieval
from pybliometrics.scopus.exception import Scopus404Error

from sosia.processing.utils import compute_overlap
from sosia.utils import print_progress


def extract_authors(pubs):
    """Get list of author IDs from a list of namedtuples representing
    publications.
    """
    l = [x.author_ids.split(";") for x in pubs if isinstance(x.author_ids, str)]
    return [int(au) for sl in l for au in sl]


def find_location(auth_ids, pubs, year):
    """Find the most common affiliation ID and country of a scientist on
    publications with valid information of the most recent year.

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

    Returns
    -------
    affiliation_id, country : str or None
        The most common affiliation_id and the most common country of the
        scientist in the year closest to the treatment year, given that
        the publications list valid information for each output.  Equals
        None when no valid publications are found.
    """
    from collections import Counter
    from operator import attrgetter
    # Available papers of most recent year with publications
    papers = [p for p in pubs if int(p.coverDate[:4]) <= year]
    papers = [p for p in papers if p.author_ids and p.author_afids]
    papers = sorted(papers, key=attrgetter("coverDate"), reverse=True)
    recent = [p for p in papers if p.coverDate[:4] == papers[0].coverDate[:4]]
    # Adff affiliation ID and geographic information of recent publications
    aff_ids = []
    countries = []
    for p in recent:
        authors = [int(a) for a in p.author_ids.split(";")]
        for focal in set(auth_ids).intersection(authors):
            idx = authors.index(focal)
        aff_ids.extend(p.author_afids.split(";")[idx].split("-"))
        countries.extend(p.affiliation_country.split(";")[idx].split("-"))
    # Find most commont ID and country
    aff_counts = Counter(aff_ids or [None])
    country_counts = Counter(countries or [None])
    aff_id = aff_counts.most_common()[0][0]
    country = country_counts.most_common()[0][0]
    return aff_id, country


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


def inform_match(profile, keywords, refresh):
    """Create namedtuple adding information to matches.

    Parameters
    ----------
    profile : sosia.Scientist()
        A Scientist() object representing a match.

    keywords : iterable of strings
        Which information to add to the match.

    refresh : bool
        Whether to refresh all cached files or not.

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
        lang = profile.get_publication_languages(refresh=refresh).language
        match_info["language"] = lang
    return match_info


def inform_matches(self, keywords, verbose, refresh):
    """Add match-specific information to all matches.

    Parameters
    ----------
    self : sosia.Original()
        Object whose matches should receive additional information.

    keywords : iterable of strings
        Which information to add to matches.

    verbose : bool
        Whether to report on the progress of the process and the completeness
        of document information.

    refresh : bool
        Whether to refresh all cached files or not.

    Returns
    -------
    out : list of namedtuples
        A list of namedtuples representing matches.  Provided information
        depend on provided keywords.
    """
    from sosia.classes import Scientist

    # Create Match object
    fields = "ID name " + " ".join(keywords)
    m = namedtuple("Match", fields)

    # Preparation
    doc_parse = "num_cited_refs" in keywords
    if doc_parse:
        focal_docs = parse_docs([d.eid for d in self.publications], refresh)
        focal_refs, focal_refs_n = focal_docs

    # Add selected information match-by-match
    out = []
    completeness = {}
    total = len(self.matches)
    print_progress(0, total, verbose)
    for idx, auth_id in enumerate(self.matches):
        period = self.year + 1 - self._period_year
        p = Scientist([auth_id], self.year, period=period, refresh=refresh,
                      sql_fname=self.sql_fname)
        match_info = inform_match(p, keywords, refresh=refresh)
        # Abstract and reference similarity is performed jointly
        if doc_parse:
            eids = [d.eid for d in p.publications]
            refs, refs_n = parse_docs(eids, refresh)
            completeness[auth_id] = (refs_n, len(eids))
            if "num_cited_refs" in keywords:
                ref_cos = compute_overlap(refs, focal_refs)
                match_info["num_cited_refs"] = ref_cos
        out.append(m(**match_info))
        print_progress(idx+1, total, verbose)

    # Eventually print information on missing information
    if verbose and doc_parse:
        for auth_id, completeness in completeness.items():
            _print_missing_docs([auth_id], completeness[0], completeness[1])
        focal_pubs_n = len(self.publications)
        _print_missing_docs(self.identifier, focal_refs_n, focal_pubs_n,
                            res_type="Original")
    return out


def parse_docs(eids, refresh):
    """Find the set of references of provided articles.

    Parameters
    ----------
    eids : list of str
        Scopus Document EIDs representing documents to be considered.

    refresh : bool
        Whether to refresh the cached files if they exist, or not.

    Returns
    -------
    refs : set
        The set of Scopus Document EIDs of cited references.

    n_valid_refs : int
        The number of documents with valid reference information.
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
    refs = set(filter(None, ref_ids))
    return refs, valid_refs


def _print_missing_docs(auth_id, n_valid_refs, total, res_type="Match"):
    """Auxiliary function to print information on missing abstracts and
    reference lists stored in a dictionary d.
    """
    auth_ids = [str(a) for a in auth_id]
    text = f"{res_type} {';'.join(auth_ids)}: {total-n_valid_refs} reference "\
           f"list(s) out of {total} documents missing"
    print(text)

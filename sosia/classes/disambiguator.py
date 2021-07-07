#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Class to handle disambiguation of a scientist."""

import re
import webbrowser
from warnings import warn
import pyperclip

import pandas as pd

from sosia.classes import Scientist
from sosia.processing import base_query

pd.set_option("display.max_rows", None, "display.max_columns", None)
pd.set_option('display.width', None)


class Disambiguator(Scientist):

    def __init__(self, identifier, in_subjects=True, homonym_fields=None,
                 limit=10, verbose=False, refresh=False, sql_fname=None):
        """Class to handle the disambiguation of scientist.

        Parameters
        ----------
        identifier : list of str
            List of Scopus Author IDs of the scientist.

        in_subjects : boolean (optional, default=True)
            Whether to restrict the search for homonyms to the same subject
            area of the scientists.

        homonym_fields : None or List (optional, default=None)
            If a list is provided, additional information is added to the list
            of homonyms. Allowed fields are: "first_year", "num_publications",
            "num_citations", "num_coauthors", "reference_sim", "abstract_sim".
            If None, will use all available fields.

        limit : int (default=10)
            The maximum number of homonyms to consider. If higher, no further
            information is downlaoded.

        refresh : boolean or int (optional, default=False)
            Whether to refresh cached results (if they exist) or not. If int
            is passed, results will be refreshed if they are older than
            that value in number of days.

        sql_fname : str (optional, default=None)
            The path of the SQLite database to connect to.  If None, will use
            the path specified in config.ini.

        Notes
        ------
        Creates three main attributes in addition to those from the
        Scientist class:
            self.homonyms_num (number of profiles with the same name)
            self.homonyms (pandas dataframe with information on homonyms)
            self.uniqueness (ratio between count of publications of the
                             scientist and the total count of publications
                             of homonyms)
        """

        if not isinstance(identifier, list):
            identifier = [identifier]
        self.identifier = [str(auth_id) for auth_id in identifier]
        self.in_subjects = in_subjects
        self.limit = limit
        self.sql_fname = sql_fname

        from datetime import datetime
        today = datetime.today()
        self.today_year = today.year

        # Instantiate superclass to load private variables
        Scientist.__init__(self, self.identifier, self.today_year, refresh=refresh,
                           sql_fname=self.sql_fname)

        # Check required information
        if not (self.surname and self.first_name):
            text = "Author profile information not found. The author identifier"\
                   f" {self.identifier} may be outdated or the profile misses"\
                   "one or both name components."
            warn(text, UserWarning)
            return None
        if not self.subjects and in_subjects:
            self.in_subjects = False
            text = "Subjects information not found. in_subjects set to False"
            warn(text, UserWarning)

        # check homonyms count
        if verbose:
            print(f"\nName: {self.name} (ID: {self.identifier})\n"\
                  "Counting homonyms...")
        first_first_name = self.first_name.split(" ")[0]
        q = f"AUTHLASTNAME({self.surname}) AND AUTHFIRST({first_first_name})"
        if in_subjects:
            _subjects_query = " OR ".join(self.subjects)
            q = q + f" AND SUBJAREA({_subjects_query})"
        _count = base_query("author", q, size_only=True, refresh=refresh)
        if verbose:
            print(f"{_count - 1} homonyms found.")
        if _count > limit + 1:
            if verbose:
                print(f"{_count - 1} homonyms found, above given limit of"\
                      f" {limit}.\n"\
                      "Homonyms information not downloaded.")
            self.uniqueness = None
            self.homonyms = pd.DataFrame()
            self.homonyms_num = _count - 1
        elif _count <= 1:
            self.uniqueness = 1
            self.homonyms = pd.DataFrame()
            self.homonyms_num = 0
            if _count == 0:
                text = "No author profile was found searching for homonyms."\
                       "The profile of the identifier provided may be outdated."
                warn(text, UserWarning)
        else:
            # download homonyms information
            if verbose:
                print("Downloading main information...")
            same_name = base_query("author", q, refresh=refresh)
            same_name = pd.DataFrame(same_name)
            same_name["ID"] = same_name.eid.str.split("-").str[-1]
            same_name = same_name.drop(columns=["eid"])
            func = self.name_compatible(verbose=verbose)
            mask1 = same_name.givenname.apply(func)
            mask2 = same_name.ID.isin(self.identifier)
            self.homonyms = (same_name[~mask2 & mask1]
                             .sort_values(by="documents", ascending=False))
            self.homonyms_num = len(self.homonyms)
            # calculate overall uniqueness
            all_pubs_count = same_name["documents"].astype(int).sum()
            self.uniqueness = len(self.publications)/all_pubs_count
            if verbose:
                print(f"{self.homonyms_num} homonyms left with compatible names.")
        if not self.homonyms.empty:
            if verbose:
                print("Adding information...")
            self.inform_homonyms(fields=homonym_fields, refresh=refresh)
            if verbose:
                print("finished.")


    def name_compatible(self, verbose=False):
        """ Returns a function (func) that test wether a name is compatible
        with the scientist name (self.first_name) based on initials. """
        def list_initials(name):
            names = [s.lower().strip() for s in re.split(r"\.| ", name)]
            return [i[0] for i in names if len(i)]

        def func(givenname, verbose=verbose):
            orig_inits = list_initials(self.first_name)
            initials = list_initials(givenname)
            unmatch_first: bool = (min(len(orig_inits), len(initials)) == 1
                                  and orig_inits[0] != orig_inits[0])
            unmatch_any: bool = (len(orig_inits) == len(initials) and
                                 len(set(orig_inits) - set(initials)))
            if unmatch_first or unmatch_any:
                if verbose:
                    print(f"{self.first_name} deemed incompatible with {givenname}.")
                return False
            return True
        return func

    def inform_homonyms(self, fields=None, verbose=False, refresh=False):
        """Add information to homonyms to aid in disambiguation process.

        Parameters
        ----------
        fields : iterable (optional, default=None)
            Which information to provide. Allowed values are "first_year",
            "num_publications", "num_citations", "num_coauthors",
            "reference_sim", "abstract_sim". If None, will
            use all available fields.

        verbose : bool (optional, default=False)
            Whether to report on the progress of the process.

        refresh : bool (optional, default=False)
            Whether to refresh cached results (if they exist) or not. If int
            is passed and stacked=False, results will be refreshed if they are
            older than that value in number of days.

        Notes
        -----
        Homonyms including corresponding information are available through
        property `.homonyms` which is a pandas dataframe.

        Raises
        ------
        fields
            If fields contains invalid keywords.
        """
        from sosia.classes import Original

        allowed_fields = ["first_year", "num_publications", "num_citations",
                          "num_coauthors", "reference_sim", "abstract_sim",
                          "cross_citations"]
        if fields:
            invalid = [x for x in fields if x not in allowed_fields]
            if invalid:
                text = "Parameter fields contains invalid keywords: " +\
                       ", ".join(invalid)
                raise ValueError(text)
        else:
            fields = allowed_fields

        if self.homonyms.empty:
            text = "No homonyms were found." \
                   "Information cannot be added."
            warn(text, UserWarning)
        else:
            scientist = Original(self.identifier, self.today_year)
            scientist.matches = self.homonyms.ID.tolist()
            scientist.inform_matches(fields=fields, verbose=verbose,
                                     refresh=refresh)
            matches = pd.DataFrame(scientist.matches)
            cols = self.homonyms.columns.tolist() + fields
            df = self.homonyms.merge(matches, on="ID")
            self.homonyms = df[cols]

    def disambiguate(self, subset=None, instructions=False, show_main=True,
                     search_cv=False):
        """
        Request user input to exclude homonyms and maintain correct IDs.

        Parameters
        ----------
        subset : None or list, optional
            If provided, the search is restricted to the subset of homonyms
            provided. If None, all are used.
        instructions : string, optional
            Alternative set of instructions to show.
        show_main : boolean, optional
            Whether to show also information about the scientist.
            The default is True.
        search_cv : boolean or list, optional
            Whehter to include search for the cv. If a list is provided,
            restrict the search to specific websites. Possible values:
            "scopus", "researchgate", "linkedin", "google". If True, all are
            used. The default is False.

        Notes
        ------
        The selected ids are added to the property self.disambiguated_ids.

        """

        def display_homonyms(homonyms):
            """Auxiliariy function to display information on homonyms."""
            homonyms_cols = self.homonyms.columns.tolist()
            select = ["ID", "documents", "surname", "givenname", "initials",
                      "affiliation", "affiliation_id", "city", "country",
                      "areas", "first_year", "reference_sim", "abstract_sim"]
            cols = [c for c in select if c in homonyms_cols]
            chunks = [homonyms[cols][i:i+3].transpose()
                      for i in range(0, len(homonyms) + 1, 3)]
            print(f"\n\nInfo on homonyms:\n"
                  f"{chunks})")

        def list_ids(action_ids, allowed_ids):
            """Auxiliariy function to generate list from user input, testing
            that the ids are included in the homonyms list."""
            ids = [i.strip() for i in action_ids.split(",")]
            for i in ids:
                if i not in allowed_ids:
                    print(f"{i} is not an ID.")
                    return None
            return ids

        def robust_input(Text):
            """Auxiliariy function to ask for user input testing if valid."""
            action = None
            while not action:
                action = input(Text)
                try:
                    action = action.split(" ")
                    if not action[0][0] in ["k", "d", "s", "g", "e", "a"]:
                        print("\nAction not valid")
                        action = None
                except (AttributeError, IndexError):
                    print("\nAction not valid")
                    action = None
            return action

        # ask to search cv
        if search_cv:
            search = ["scopus", "researchgate", "linkedin", "google"]
            if isinstance(search_cv, list):
                search = search_cv
            self.search_cv(search=search)

        # prepare elements to screen
        self.disambiguated_ids = self.identifier.copy()
        if self.homonyms_num == 0:
            print("Already unique")
            return None

        homonyms = self.homonyms
        if subset:
            homonyms = self.homonyms[homonyms.ID.isin(subset)]
        if homonyms.empty:
            raise Exception("Subset is empty")

        display_instructions =\
               "\n\nAs action, type:\n"\
               "'(k)eep' to keep all homonyms.\n"\
               "'(d)rop' to drop all homonyms\n"\
               "'(s)copus' to browse all homonyms in Scopus\n"\
               "'(g)oogle' to browse name and affilaition in Google\n"\
               "'(e)xit' to exit (current results preserved)\n"\
               "'(a)bort' to stop AND reset results)\n"\
               "Add space and a comma-sep list of homonyms to perform "\
               "an action on a subset."
        if instructions:
            # overwrite instructions
            display_instructions = instructions

        # do screening asking user input
        if show_main:
            self.display_main()
            action = input("Type (s)copus or (g)oogle to browse, or continue: ")
            while action and action[0] in ["s", "g"]:
                if action and action[0] == "s":
                    browse([self.identifier])
                    action = input("Type (s)copus or (g)oogle to browse, "\
                                   "or continue: ")
                if action and action[0] == "g":
                    info = (self.first_name + " " + self.surname +
                            " " + self.last_affiliation)
                    browse([info], search="google")
                    action = input("Type (s)copus or (g)oogle to browse, "\
                                   "or continue: ")

        print(display_instructions)
        display_homonyms(homonyms)
        action = robust_input("action: ")
        while action[0][0] != "e":
            if action[0][0] == "k":
                # keep all or provided list of homonyms
                ids = homonyms.ID.tolist()
                if len(action) > 1:
                    ids = list_ids(action[1], homonyms.ID.tolist())
                    if not ids:
                        action = robust_input("action: ")
                        continue
                    # save partial results and continue screening
                    self.disambiguated_ids.extend(ids)
                    homonyms = homonyms[~homonyms.ID.astype(str).isin(ids)]
                    display_homonyms(homonyms)
                    action = robust_input("action: ")
                    continue
                # else save all and exit
                self.disambiguated_ids.extend(ids)
                action = "e"
                continue
            if action[0][0] == "d":
                # drop all or provided list of homonyms
                if len(action) > 1:
                    ids = list_ids(action[1], homonyms.ID.tolist())
                    if not ids:
                        action = robust_input("action: ")
                        continue
                    # remove rejected and keep screening (or exit)
                    homonyms = homonyms[~homonyms.astype(str).ID.isin(ids)]
                    print(f"{ids} rejected")
                    display_homonyms(homonyms)
                    action = robust_input("action: ")
                    if action == "e":
                        accept = robust_input("Accept all others? (y)es or (n)o: ")
                        if accept[0] == "y":
                            self.disambiguated_ids.extend(homonyms.ID.tolist())
                    continue
                action = "e"
            if action[0][0] == "s":
                # browse in scopus all or the provided list of homonyms
                ids = homonyms.ID.tolist()
                if len(action) > 1:
                    allowed = homonyms.ID.tolist() + self.identifier
                    ids = list_ids(action[1], allowed)
                    if not ids:
                        action = robust_input("action: ")
                        continue
                browse([[i] for i in ids])
                action = robust_input("action: ")
                continue
            if action[0][0] == "g":
                # search in Google all or the provided list of homonyms
                ids = homonyms.ID.tolist()
                if len(action) > 1:
                    allowed = homonyms.ID.tolist() + self.identifier
                    ids = list_ids(action[1], allowed)
                    if not ids:
                        action = robust_input("action: ")
                        continue
                info = (homonyms[homonyms.ID.isin(ids)]
                        [["givenname", "surname", "affiliation"]]
                        .fillna('')
                        .agg(' '.join, axis=1))
                browse(info.tolist(), search="google")
                action = robust_input("action: ")
                continue
            if action[0][0] == "a":
                # abort
                self.disambiguated_ids = None
                action = "e"
                continue

    def display_main(self):
        """ Auxiliariy function to display information on scientist """
        _dict = {"ID": self.identifier,
                 "documents": len(self.publications),
                 "surname": self.surname,
                 "givenname": self.first_name,
                 "initials": self.initials,
                 "affiliation": self.last_affiliation,
                 "affiliation_id": self.affiliation_id,
                 "city": self.last_city,
                 "country": self.last_country,
                 "areas": self.subjects,
                 "first_year": self.first_year}
        print(f"Info of main identifier ({self.identifier}):\n"
              f"{pd.Series(_dict)})\n")

    def search_cv(self, search=True):
        """
        Search cv of scientists browsing different websites. A file name is
        copied to the clipboard.

        Parameters
        ----------
        search : True or list, optional
            If a list is provided, the search is restricted to specific
            websites. Possible values: "scopus", "researchgate", "linkedin",
            "google". The default is True.

        """
        info = (self.first_name + " " + self.surname +
                " " + self.last_affiliation)
        file_id = (self.name.replace(", ", "_") + "_"
                   + "_".join(self.identifier))
        self.cv_file_id = file_id
        pyperclip.copy(file_id)
        print("Search cv file for:")
        self.display_main()
        print(f"\nFile name copied to clipboard: {file_id}")
        input("Press enter to start search: ")
        search = ["scopus", "researchgate", "linkedin", "google"]
        if isinstance(search, list):
            search = search
        for s in search:
            browse([info], search=s)
        cv_link = input("Input link to most complete CV or enter to continue: ")
        if cv_link:
            self.cv_link = cv_link


def browse(info, search="scopus"):
    """ Auxiliary function to search information about an author in Scopus or
    Google """
    def build_url(author, search):
        if search == "scopus":
            query = "%29+OR+AU-ID%28".join(author)
            url = ("https://www.scopus.com/results/results.uri?sort=plf-f&src=s&sid=df23"
                  "e895a945c5d150a7d829b5a47050&sot=a&sdt=a&sl=18&s=AU-ID%28{}%29&origin"
                  "=searchadvanced&editSaveSearch=&txGid=dbcb197305252cc57294a2ad6355bbd1"
                  .format(query))
        if search == "google":
            url = "https://www.google.com.tr/search?q={}".format(author)
        if search == "linkedin":
            url = ("https://www.linkedin.com/search/results/all/?keywords="
                   "{}&origin=GLOBAL_SEARCH_HEADER").format(author)
        if search == "researchgate":
            url = ("https://www.researchgate.net/search.Search.html?type="\
                   "researcher&query={}").format(author)
        return url
    for author in info:
        webbrowser.open(build_url(author, search), new=2)

import sys
import os
from datetime import date

cwd = os.getcwd()
project_root = os.path.dirname(cwd)
sys.path.insert(0, project_root)

# -- Project information -----------------------------------------------------

project = "sosia"
author = "Michael E. Rose and Stefano H. Baruffaldi"
copyright = f"2017-{date.today().year} {author}"

import sosia

version = sosia.__version__
release = sosia.__version__
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    'sphinx_copybutton'
]
copybutton_prompt_text = ">>> "
autodoc_member_order = "groupwise"
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
language = 'en'
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = "sphinx"


# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"
html_theme_options = {
    "github_user": "sosia-dev",
    "github_repo": "sosia",
    "github_banner": "true",
    "github_button": "true",
    "github_type": "star",
}
html_static_path = ["_static"]
html_sidebars = {"**": ["about.html", "navigation.html", "searchbox.html"]}


# -- Options for HTMLHelp output ---------------------------------------------

html_show_sourcelink = True
autoclass_content = "both"

htmlhelp_basename = "sosiadoc"


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

latex_documents = [
    (
        master_doc,
        "sosia.tex",
        "sosia Documentation",
        "Michael E. Rose and Stefano H. Baruffaldi",
        "manual",
    )
]


# -- Options for manual page output ------------------------------------------

man_pages = [(master_doc, "sosia", "sosia Documentation", [author], 1)]


# -- Options for Texinfo output ----------------------------------------------

texinfo_documents = [
    (
        master_doc,
        "sosia",
        "sosia Documentation",
        author,
        "sosia",
        "One line description of project.",
        "Miscellaneous",
    )
]


# -- Options for Epub output -------------------------------------------------

epub_title = project

epub_exclude_files = ["search.html"]


# -- Extension configuration -------------------------------------------------

# -- Options for intersphinx extension ---------------------------------------

intersphinx_mapping = {"https://docs.python.org/": None}

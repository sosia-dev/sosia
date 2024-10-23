Match Authors in Scopus automatically with sosia
================================================

`sosia` (Italian for *doppelgänger*) finds researchers that are similar to another one. Use the matching researcher as a control in Diff-in-Diff anlyses. sosia is developed and `described <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3742602>`_ by econometricians for scientists of science.

`sosia` does not pre-compute annual characteristics to find controls as in Coarsened Exact Matching. Instead, `sosia` searches the entire Scopus database via `pybliometrics <https://pybliometrics.readthedocs.io/en/latest/index.html>`_. Once `pybliometrics` is configured (Scopus access key, etc.), let `sosia` find a match for you.

=======
Example
=======

Install sosia from PyPI using the console or command line interpreter:

.. code-block:: console

    $ pip install sosia

In Python, set up `sosia` (and eventually `pybliometrics`) and search for similar scientists using their Scoups Author Profile IDs.

.. include:: ../README.rst
  :start-after: inclusion-marker-start
  :end-before: inclusion-marker-end


Full reference:

.. currentmodule:: sosia

.. autosummary::

    Original

========
Citation
========

If `sosia` helped you getting data for research, please cite our corresponding paper:

* Rose, Michael E. and Stefano H. Baruffaldi: "`Finding Doppelgängers in Scopus: How to Build Scientists Control Groups Using Sosia <https://papers.ssrn.com/abstract=3742602>`_", Max Planck Institute for Innovation & Competition Research Paper No. 20-20.

Citing the paper helps the development of `sosia`, because it justifies funneling resources into the development.  It also signals that you created your control group in a transparent and replicable way.


==================
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. Hidden links for Navigation side panel
.. toctree::
   :maxdepth: 2
   :hidden:

   functioning
   tutorial
   reference
   changelog
   authors
   contributing

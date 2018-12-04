eprints2bag<img width="100px" align="right" src=".graphics/noun_bag_1002779.svg">
=========

A program for downloading records from the [Caltech Collection of Open Digital Archives (CODA)](https://libguides.caltech.edu/CODA) Eprints server and creating [BagIt](https://en.wikipedia.org/wiki/BagIt) bags out of them.

*Authors*:      [Michael Hucka](http://github.com/mhucka), [Betsy Coles](https://github.com/betsycoles)<br>
*Repository*:   [https://github.com/caltechlibrary/eprints2bag](https://github.com/caltechlibrary/eprints2bag)<br>
*License*:      BSD/MIT derivative &ndash; see the [LICENSE](LICENSE) file for more information

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg?style=flat-square)](https://choosealicense.com/licenses/bsd-3-clause)
[![Python](https://img.shields.io/badge/Python-3.4+-brightgreen.svg?style=flat-square)](http://shields.io)
[![Latest release](https://img.shields.io/badge/Latest_release-0.0.1-b44e88.svg?style=flat-square)](http://shields.io)

Table of Contents
-----------------

* [Introduction](#-introduction)
* [Installation instructions](#-installation-instructions)
* [Running eprints2bag](#︎-running-eprints2bag)
* [Getting help and support](#-getting-help-and-support)
* [History](#✍︎-history)
* [Acknowledgments](#︎-acknowledgments)
* [Copyright and license](#︎-copyright-and-license)

☀ Introduction
-----------------------------

Materials in EPrints must be extracted before they can be moved to a preservation system such as [DPN](https://dpn.org) or another long-term storage or dark archive.  _Eprints2bag_ encapsulates the processes needed to gather the materials and bundle them up in  [BagIt](https://en.wikipedia.org/wiki/BagIt) bags.  You indicate which records from CODA you want (based on record numbers), and it will download the content and bag it up.  Eprints2bag is a command-line tool written in Python 3.


✺ Installation instructions
---------------------------

⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/eprints2bag/issues) for this repository.


★ Do you like it?
------------------

If you like this software, don't forget to give this repo a star on GitHub to show your support!


✍︎ History
--------

In 2018, [Betsy Coles](https://github.com/betsycoles) wrote a set of Perl scripts and described a workflow for bagging content from Caltech's Eprints-based [Caltech Collection of Open Digital Archives (CODA)](https://libguides.caltech.edu/CODA) server.  The original code is still available in this repository in the [historical](historical) subdirectory.  In late 2018, Mike Hucka sought to expand the functionality of the original _eprints2dpn_ tools and generalize them in anticipation of having to stop using DPN because on 2018-12-04, DPN announced they were shutting down. Thus was born _eprints2bag_.


☺︎ Acknowledgments
-----------------------

The [vector artwork](https://thenounproject.com/search/?q=bag&i=1002779) of a bag used as a logo for Eprints2bag was created by [StoneHub](https://thenounproject.com/stonehub/) from the Noun Project.  It is licensed under the Creative Commons [CC-BY 3.0](https://creativecommons.org/licenses/by/3.0/) license.

Eprints2bag makes use of numerous open-source packages, without which it would have been effectively impossible to develop Turf with the resources we had.  We want to acknowledge this debt.  In alphabetical order, the packages are:

* [colorama](https://github.com/tartley/colorama) &ndash; makes ANSI escape character sequences work under MS Windows terminals
* [halo](https://github.com/ManrajGrover/halo) &ndash; busy-spinners for Python command-line programs
* [ipdb](https://github.com/gotcha/ipdb) &ndash; the IPython debugger
* [plac](http://micheles.github.io/plac/) &ndash; a command line argument parser
* [requests](http://docs.python-requests.org) &ndash; an HTTP library for Python
* [setuptools](https://github.com/pypa/setuptools) &ndash; library for `setup.py`
* [termcolor](https://pypi.org/project/termcolor/) &ndash; ANSI color formatting for output in terminal

☮︎ Copyright and license
---------------------

Copyright (C) 2018, Caltech.  This software is freely distributed under a BSD/MIT type license.  Please see the [LICENSE](LICENSE) file for more information.
    
<div align="center">
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src=".graphics/caltech-round.svg">
  </a>
</div>

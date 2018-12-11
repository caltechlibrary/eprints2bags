eprints2bags<img width="100px" align="right" src=".graphics/noun_bag_1002779.svg">
=========

A program for downloading records from an Eprints server and creating [BagIt](https://en.wikipedia.org/wiki/BagIt) bags out of them.

*Authors*:      [Michael Hucka](http://github.com/mhucka), [Betsy Coles](https://github.com/betsycoles)<br>
*Repository*:   [https://github.com/caltechlibrary/eprints2bags](https://github.com/caltechlibrary/eprints2bags)<br>
*License*:      BSD/MIT derivative &ndash; see the [LICENSE](LICENSE) file for more information

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg?style=flat-square)](https://choosealicense.com/licenses/bsd-3-clause)
[![Python](https://img.shields.io/badge/Python-3.4+-brightgreen.svg?style=flat-square)](http://shields.io)
[![Latest release](https://img.shields.io/badge/Latest_release-1.2.0-b44e88.svg?style=flat-square)](http://shields.io)

Table of Contents
-----------------

* [Introduction](#-introduction)
* [Installation instructions](#-installation-instructions)
* [Running eprints2bags](#︎-running-eprints2bags)
* [Getting help and support](#-getting-help-and-support)
* [History](#✍︎-history)
* [Acknowledgments](#︎-acknowledgments)
* [Copyright and license](#︎-copyright-and-license)

☀ Introduction
-----------------------------

Materials in EPrints must be extracted before they can be moved to a preservation system such as [DPN](https://dpn.org) or another long-term storage or dark archive.  _Eprints2bags_ encapsulates the processes needed to gather the materials and bundle them up in [BagIt](https://en.wikipedia.org/wiki/BagIt) bags.  The program works over a network using an EPrints server's REST API.  It downloads a subset of records or all records, and bags them up individually.  Eprints2bags is a command-line tool written in Python 3.


✺ Installation instructions
---------------------------

The following is probably the simplest and most direct way to install this software on your computer, as well as update an existing copy if you have already installed eprints2bags and a new version has been released:
```sh
sudo python3 -m pip install git+https://github.com/caltechlibrary/eprints2bags.git --upgrade
```

Alternatively, you can instead clone this GitHub repository and then run `setup.py` manually.  First, create a directory somewhere on your computer where you want to store the files, and cd to it from a terminal shell.  Next, execute the following commands:
```sh
git clone https://github.com/caltechlibrary/eprints2bags.git
cd eprints2bags
sudo python3 -m pip install . --upgrade
```

▶︎ Running eprints2bags
---------------------

This program contacts an EPrints REST server whose network API is accessible at the URL given by the command-line option `-a` (or `/a` on Windows).  A typical EPrints server URL has the form `https://server.institution.edu/rest`.  The `-a` (or `/a`) option is required; the program cannot infer the server address on its own.

If given the option `-f` (or `/f` on Windows), the records retrieved from the EPrints server will be limited to the list of records indicated by the value given to the option.  The value of `-f` can be file, in which case the file is assumed to contain EPrints identifier numbers (integers), one per line of the file.  Alternatively, the value of the topion can be one or more integers separated by commas (e.g., `-f 54602,54604`), or a range of numbers separated by a dash (e.g., `-f 1-100`, which is interpreted as the list of numbers 1, 2, ..., 100 inclusive).  In those cases, the records written will be limited to those numbered.  If no `-f` option is given at all, this program will download all the contents available at the given EPrints server.

By default, if a record requested or implied by the arguments to `-f` is missing from the EPrints server, this **will count as an error** and stop execution of the program.  If the option `-m` (or `/m` on Windows) is given, missing records will be ignored.  Option `-m` is particularly useful when giving a range of numbers with the `-f` option, as it is common for EPrints records to be updated or deleted and gaps to be left in the numbering.

This program writes the output in the directory given by the command-line option `-o` (or `/o` on Windows).  If the directory does not exist, this program will create it.  If the directory does exist, it will be overwritten with the new content.  The result of running this program will be individual directories underneath the directory given by the `-o` option, with each subdirectory named according to the EPrints record number (e.g., `/path/to/output/430`, `/path/to/output/431`, `/path/to/output/432`, ...).  If the `-b` option (`/b` on Windows) is given, the subdirectory names are changed to have the form _BASENAME-NUMBER_ where _BASENAME_ is the text string provided with the `-b` option and the _NUMBER_ is the EPrints number for a given entry.


### Content gathered and output produced

Each directory created by `eprints2bags` will contain an EP3XML XML file and additional document file(s) associated with the EPrints record in question.  The list of documents for each record is determined from XML file, in the `<documents>` element.  Certain EPrints internal documents such as `indexcodes.txt` and `preview.png` are ignored.

Downloading some documents may require supplying a user login and password to the EPrints server.  These can be supplied using the command-line arguments `-u` and `-p`, respectively (`/u` and `/p` on Windows).

After downloading a complete record from EPrints, this program creates [BagIt](https://en.wikipedia.org/wiki/BagIt) bags from the contents of the subdirectories created for each record, then creates a [gzip](https://www.gnu.org/software/gzip/)'ed [tar](https://www.gnu.org/software/tar/) archive the bag directory.  This is done by default, after the documents are downloaded for each record, unless the `-B` option (`/B` on Windows) is given.  Note that creating bags is a destructive operation: it replaces the individual directories of each record with a restructured directory corresponding to the BagIt format.


### Examples

On Linux and macOS systems, assuming that the installation proceeds normally, you should end up with a program called `eprints2bags` in a location normally searched by your terminal shell for commands.  Running eprints2bags then consists of invoking the program like any other program on your system.

The following is a simple example showing how to get a single record (#85447) from Caltech's [CODA](https://libguides.caltech.edu/CODA) Eprints server (with user name and password blanked out here for security reasons):

```
# eprints2bags -o /tmp/eprints -f 85447 -a https://authors.library.caltech.edu/rest -u XXXXX -p XXXXX

Beginning to process 1 EPrints entry.
Output will be written under directory "/tmp/eprints"
======================================================================
Getting record with id 85447
Creating /tmp/eprints/85447
Downloading https://authors.library.caltech.edu/85447/1/1-s2.0-S0164121218300517-main.pdf
Making bag out of /tmp/eprints/85447
Creating tarball /tmp/eprints/85447.tgz
======================================================================
Done. Wrote 1 EPrints records to /tmp/eprints/.
```

### Summary of command-line options

The following table summarizes all the command line options available. (Note: on Windows computers, `/` must be usedas the prefix character instead of `-`):

| Short   | Long&nbsp;form&nbsp;opt | Meaning | Default |  |
|---------|-------------------|----------------------|---------|---|
| `-a`_A_ | `--api-url`_A_    | Use _A_ as the server's REST API URL | | ⚑ |
| `-b`_B_ | `--base-name`_B_  | Name outputs with the template _B_-n | Use only the record number n  | |
| `-d`_D_ | `--delay`_D_      | Pause _D_ ms between records | 100 | |
| `-f`_F_ | `--fetch-list`_F_ | Read record numbers from _F_ | Fetch all records from the server | |
| `-m`    | `--missing-ok`    | Don't count missing records as an error | Stop if missing record encountered | |
| `-o`_O_ | `--output-dir`_O_ | Write outputs to directory _O_ |  |  ⚑ |
| `-u`_U_ | `--user`_U_       | User name for EPrints server login | |
| `-p`_P_ | `--password`_U_   | Password for EPrints proxy login | |
| `-q`    | `--quiet`         | Don't print info messages while working | Be chatty while working | |
| `-B`    | `--no-bags`       | Don't create BagIt bags | Bag up the records | |
| `-C`    | `--no-color`      | Don't color-code the output | Use colors in the terminal output | |
| `-K`    | `--no-keyring`    | Don't color-code the output | Use colors in the terminal output | |
| `-D`    | `--debug`         | Debugging mode | Normal mode | |
| `-R`    | `--reset`         | Reset user login & password used | Reuse previously-used credentials |
| `-V`    | `--version`       | Print program version info and exit | Do other actions instead | |

 ⚑ &nbsp; Required argument.


### Additional notes and considerations

Beware that some file systems have limitations on the number of subdirectories that can be created, which directly impacts how many record subdirectories can be created by this program.  In particular, note that Linux ext2 and ext3 file systems are limited to 31,998 subdirectories.  This means you cannot grab more than 32,000 entries at a time from an EPrints server.

It is also noteworthy that hitting a server for tens of thousands of records and documents in rapid succession is likely to draw suspicion from server administrators.  By default, this program inserts a small delay between record fetches (adjustable using the `-d` command-line option), which may be too short in some cases.  Setting the value to 0 is also possible, but might get you blocked or banned from an institution's servers.


⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/eprints2bags/issues) for this repository.


★ Do you like it?
------------------

If you like this software, don't forget to give this repo a star on GitHub to show your support!


✍︎ History
--------

In 2018, [Betsy Coles](https://github.com/betsycoles) wrote a [set of Perl scripts](https://github.com/caltechlibrary/eprints2dpn) and described a workflow for bagging content from Caltech's Eprints-based [Caltech Collection of Open Digital Archives (CODA)](https://libguides.caltech.edu/CODA) server.  The original code is still available in this repository in the [historical](historical) subdirectory.  In late 2018, Mike Hucka sought to expand the functionality of the original tools and generalize them in anticipation of having to stop using DPN because on 2018-12-04, DPN announced they were shutting down. Thus was born _eprints2bags_.


☺︎ Acknowledgments
-----------------------

The [vector artwork](https://thenounproject.com/search/?q=bag&i=1002779) of a bag used as a logo for Eprints2bags was created by [StoneHub](https://thenounproject.com/stonehub/) from the Noun Project.  It is licensed under the Creative Commons [CC-BY 3.0](https://creativecommons.org/licenses/by/3.0/) license.

Eprints2bags makes use of numerous open-source packages, without which it would have been effectively impossible to develop Turf with the resources we had.  We want to acknowledge this debt.  In alphabetical order, the packages are:

* [bagit]() &ndash; 
* [colorama](https://github.com/tartley/colorama) &ndash; makes ANSI escape character sequences work under MS Windows terminals
* [ipdb](https://github.com/gotcha/ipdb) &ndash; the IPython debugger
* [keyring](https://github.com/jaraco/keyring) &ndash; access the system keyring service from Python
* [lxml](https://lxml.de) &ndash; an XML parsing library for Python
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

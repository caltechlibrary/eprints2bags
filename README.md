eprints2bags<img width="100px" align="right" src="https://raw.githubusercontent.com/caltechlibrary/eprints2bags/main/.graphics/eprints2bags.png">
=========

A program for downloading records from an EPrints server and creating [BagIt](https://en.wikipedia.org/wiki/BagIt) packages out of them.

*Authors*:      [Michael Hucka](http://github.com/mhucka), [Betsy Coles](https://github.com/betsycoles)<br>
*Repository*:   [https://github.com/caltechlibrary/eprints2bags](https://github.com/caltechlibrary/eprints2bags)<br>
*License*:      BSD/MIT derivative &ndash; see the [LICENSE](LICENSE) file for more information

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg?style=flat-square)](https://choosealicense.com/licenses/bsd-3-clause)
[![Python](https://img.shields.io/badge/Python-3.5+-brightgreen.svg?style=flat-square)](http://shields.io)
[![Latest release](https://img.shields.io/github/v/release/caltechlibrary/eprints2bags.svg?style=flat-square&color=b44e88)](https://github.com/caltechlibrary/eprints2bags/releases)
[![DOI](http://img.shields.io/badge/DOI-10.22002%20%2f%20D1.1450-blue.svg?style=flat-square)](https://data.caltech.edu/records/20082)
[![PyPI](https://img.shields.io/pypi/v/eprints2bags.svg?style=flat-square&color=red)](https://pypi.org/project/eprints2bags/)


Table of Contents
-----------------

* [Introduction](#-introduction)
* [Installation instructions](#-installation-instructions)
* [Using eprints2bags](#︎-using-eprints2bags)
* [Getting help and support](#-getting-help-and-support)
* [Do you like it?](#-do-you-like-it)
* [Contributing — info for developers](#-contributing--info-for-developers)
* [History](#-history)
* [Acknowledgments](#︎-acknowledgments)
* [Copyright and license](#︎-copyright-and-license)


☀ Introduction
-----------------------------

Materials in EPrints must be extracted before they can be moved to a long-term preservation system or dark archive.  _Eprints2bags_ is a self-contained program that encapsulates the processes needed to download records and documents from EPrints, bundle up individual records in [BagIt](https://en.wikipedia.org/wiki/BagIt) packages, and create single-file archives (e.g., in [ZIP](https://en.wikipedia.org/wiki/Zip_(file_format)) format) of each bag.  The program is written in Python 3 and works over a network using an EPrints server's REST API.


✺ Installation instructions
---------------------------

The instructions below assume you have a Python interpreter installed on your computer; if that's not the case, please first install Python and familiarize yourself with running Python programs on your system.

On **Linux**, **macOS**, and **Windows** operating systems, you should be able to install `eprints2bags` with [`pip`](https://pip.pypa.io/en/stable/installing/).  If you don't have the `pip` package or are uncertain if you do, first run the following command in a terminal command line interpreter: 
```
sudo python3 -m ensurepip
```

Then, to install `eprints2bags` from the Python package repository, run the following command:
```
python3 -m pip install eprints2bags --user --upgrade
```

As an alternative to getting it from PyPI, you can instruct `pip` to install `eprints2bags` directly from the GitHub repository:
```sh
python3 -m pip install git+https://github.com/caltechlibrary/eprints2bags.git --user --upgrade
```

On Linux and macOS systems, assuming that the installation proceeds normally, you should end up with a program called `eprints2bags` in a location normally searched by your terminal shell for commands.


▶︎ Using Eprints2bags
---------------------

For help with usage at any time, run `eprints2bags` with the option `-h` (or `/h` on Windows).

`eprints2bags` contacts an EPrints REST server whose network API is accessible at the URL given by the command-line option `-a` (or `/a` on Windows).  A typical EPrints server URL has the form `https://somename.yourinstitution.edu/rest`.  **This program will automatically add `/eprint` to the URL path given**, so omit that part of the URL in the value given to `-a`.  The `-a` (or `/a`) option is required; the program cannot infer the server address on its own.


### _Specifying which records to get_

The EPrints records to be written will be limited to the list of EPrints numbers found in the file given by the option `-i` (or `/i` on Windows).  If no `-i` option is given, this program will download all the contents available at the given EPrints server.  The value of `-i` can also be one or more integers separated by commas (e.g., `-i 54602,54604`), or a range of numbers separated by a dash (e.g., `-i 1-100`, which is interpreted as the list of numbers 1, 2, ..., 100 inclusive), or some combination thereof.  In those cases, the records written will be limited to those numbered.

If the `-l` option (or `/l` on Windows) is given, the records will be additionally filtered to return only those whose last-modified date/time stamp is no older than the given date/time description.  Valid descriptors are those accepted by the Python [dateparser](https://pypi.org/project/dateparser/) library.  Make sure to enclose descriptions within single or double quotes.  Examples:

```
eprints2bags -l "2 weeks ago" -a ....
eprints2bags -l "2014-08-29"  -a ....
eprints2bags -l "12 Dec 2014" -a ....
eprints2bags -l "July 4, 2013" -a ....
```

If the `-s` option (or `/s` on Windows) is given, the records will also be filtered to include only those whose `<eprint_status>` element value is one of the listed status codes.  Comparisons are done in a case-insensitive manner.  Putting a caret character (`^`) in front of the status (or status list) negates the sense, so that `eprints2bags` will only keep those records whose `<eprint_status>` value is _not_ among those given.  Examples:

```
eprints2bags -s archive -a ...
eprints2bags -s ^inbox,buffer,deletion -a ...
```

Both lastmod and status filering are done after the `-i` argument is processed.

By default, if an error occurs when requesting a record from the EPrints server, it stops execution of `eprints2bags`.  Common causes of errors include missing records implied by the arguments to `-i`, missing files associated with a given record, and files inaccessible due to permissions errors.  If the option `-k` (or `/k` on Windows) is given, `eprints2bags` will attempt to keep going upon encountering missing records, or missing files within records, or similar errors.  Option `-k` is particularly useful when giving a range of numbers with the `-i` option, as it is common for EPrints records to be updated or deleted and gaps to be left in the numbering.  (Running without `-i` will skip over gaps in the numbering because the available record numbers will be obtained directly from the server, which is unlike the user providing a list of record numbers that may or may not exist on the server.  However, even without `-i`, errors may still result from permissions errors or other causes.)


### _Specifying what to do with the records_

This program writes its output in subdirectories under the directory given by the command-line option `-o` (or `/o` on Windows).  If the directory does not exist, this program will create it.  If no `-o` is given, the current directory where `eprints2bags` is running is used.  Whatever the destination is, `eprints2bags` will create subdirectories in the destination, with each subdirectory named according to the EPrints record number (e.g., `/path/to/output/43`, `/path/to/output/44`, `/path/to/output/45`, ...).  If the `-n` option (`/n` on Windows) is given, the subdirectory names are changed to have the form _NAME-NUMBER__ where _NAME_ is the text string provided to the `-n` option and the _NUMBER_ is the EPrints number for a given entry (meaning, `/path/to/output/NAME-43`, `/path/to/output/NAME-44`, `/path/to/output/NAME-45`, ...).

Each directory will contain an [EPrints XML](https://wiki.eprints.org/w/XML_Export_Format) file and additional document file(s) associated with the EPrints record in question.  Documents associated with each record will be fetched over the network.  The list of documents for each record is determined from XML file, in the `<documents>` element.  Certain EPrints internal documents such as `indexcodes.txt` and preview images are ignored.

By default, each record and associated files downloaded from EPrints will be placed in a directory structure that follows the [BagIt](https://en.wikipedia.org/wiki/BagIt) specification, and then this bag will then be put into its own single-file archive.  The default archive file format is [ZIP](https://en.wikipedia.org/wiki/Zip_(file_format)) with compression turned off (see next paragraph).  Option `-b` (`/b` on Windows) can be used to change this behavior.  This option takes a keyword value; possible values are `none`, `bag` and `bag-and-archive`, with the last being the default.  Value `none` will cause `eprints2bags` to leave the downloaded record content in individual directories without bagging or archiving, and value `bag` will cause `eprints2bags` to create BagIt bags but not single-file archives from the results.  Everything will be left in the output directory (the location given by the `-o` or `/o` option).  Note that creating bags is a destructive operation: it replaces the individual directories of each record with a restructured directory corresponding to the BagIt format.

The type of archive made when `bag-and-archive` mode is used for the `-b` option can be changed using the option `-t` (or `/t` on Windows).  The possible values are: `compressed-zip`, `uncompressed-zip`, `compressed-tar`, and `uncompressed-tar`.  As mentioned above, the default is `uncompressed-zip` (used if no `-t` option is given).  [ZIP](https://en.wikipedia.org/wiki/Zip_(file_format)) is the default because it is more widely recognized and supported than [tar](https://en.wikipedia.org/wiki/Tar_(computing)) format, and _uncompressed_ ZIP is used because file corruption is generally more damaging to a compressed archive than an uncompressed one.  Since the main use case for `eprints2bags` is to archive contents for long-term storage, avoiding compression seems safer.

The ZIP archive file will be written with a text comment describing the contents of the archive.  This comment can be viewed by ZIP utilities (e.g., using `zipinfo -z` on Unix/Linux and macOS).  The following is an example of a comment and the information it contains:

```
~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
About this archive file:

This is an archive of a file directory organized in BagIt v1.0 format.
The bag contains the content from the EPrints record located at
http://resolver.caltech.edu/CaltechAUTHORS:SHIjfm98

The software used to create this archive file was:
eprints2bags version 1.3.1 <https://github.com/caltechlibrary/eprints2bags>

The following is the metadata contained in bag-info.txt:
Bag-Software-Agent: bagit.py v1.7.0 <https://github.com/LibraryOfCongress/bagit-python>
Bagging-Date: 2018-12-13
External-Description: Archive of EPrints record and document files
External-Identifier: http://resolver.caltech.edu/CaltechAUTHORS:SHIjfm98
Internal-Sender-Identifier: https://authors.library.caltech.edu/id/eprint/355
Payload-Oxum: 4646541.2
~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
```

Archive comments are a feature of the [ZIP](https://en.wikipedia.org/wiki/Zip_(file_format)) file format and not available with [tar](https://en.wikipedia.org/wiki/Tar_(computing)).

Finally, the overall collection of EPrints records (whether the records are bagged and archived, or just bagged, or left as-is) can optionally be itself put into a bag and/or put in a ZIP archive.  This behavior can be changed with the option `-e` (`/e` on Windows).  Like `-b`, this option takes the possible values `none`, `bag`, and `bag-and-archive`.  The default is `none`.  If the value `bag` is used, a top-level bag containing the individual EPrints bags is created out of the output directory (the location given by the `-o` option); if the value `bag-and-archive` is used, the bag is also put into a single-file archive.  (In other words, the result will be a ZIP archive of a bag whose data directory contains other ZIP archives of bags.)  For safety, `eprints2bags` will refuse to do `bag` or `bag-and-archive` unless a separate output directory is given via the `-o` option; otherwise, this would restructure the current directory where `eprints2bags` is running &ndash; with potentially unexpected or even catastrophic results.  (Imagine if the current directory were the user's home directory!)

Generating checksum values can be a time-consuming operation for large bags.  By default, during the bagging step, `eprints2bags` will use a number of processes equal to one-half of the available CPUs on the computer.  The number of processes can be changed using the option `-c` (or `/c` on Windows).

The use of separate options for the different stages provides some flexibility in choosing the final output.  For example,

```
eprints2bags --bag-action none --end-action bag-and-archive
```

will create a ZIP archive containing a single bag directory whose `data/` subdirectory contains the set of (unbagged) EPrints records retrieved by `eprints2bags` from the server.

### _Server credentials_

Downloading documents usually requires supplying a user login and password to the EPrints server.  By default, this program uses the operating system's keyring/keychain functionality to get a user name and password.  If the information does not exist from a previous run of `eprints2bags`, it will query the user interactively for the user name and password, and unless the `-K` argument (`/K` on Windows) is given, store them in the user's keyring/keychain so that it does not have to ask again in the future.  It is also possible to supply the information directly on the command line using the `-u` and `-p` options (or `/u` and `/p` on Windows), but this is discouraged because it is insecure on multiuser computer systems.

If a given EPrints server does not require a user name and password, do not use `-u` or `-p` and leave the name and password blank when prompted for them by `eprints2bags`.  Empty user name and password are allowed values.

To reset the user name and password (e.g., if a mistake was made the last time and the wrong credentials were stored in the keyring/keychain system), add the `-R` (or `/R` on Windows) command-line argument to a command.  When `eprints2bags` is run with this option, it will query for the user name and password again even if an entry already exists in the keyring or keychain.


### _Other options_

`eprints2bags` produces color-coded diagnostic output as it runs, by default.  However, some terminals or terminal configurations may make it hard to read the text with colors, so `eprints2bags` offers the `-C` option (`/C` on Windows) to turn off colored output.

If given the `-@` argument (`/@` on Windows), this program will output a detailed trace of what it is doing, and will also drop into a debugger upon the occurrence of any errors.  The debug trace will be written to the given destination, which can be a dash character (`-`) to indicate console output, or a file path.

If given the `-V` option (`/V` on Windows), this program will print the version and other information, and exit without doing anything else.


### _Basic usage examples_

Running `eprints2bags` then consists of invoking the program like any other program on your system.  The following is a simple example showing how to get a single record (#85447) from Caltech's [CODA](https://libguides.caltech.edu/CODA) EPrints server (with user name and password blanked out here for security reasons):

```
# eprints2bags -o /tmp/eprints -i 85447 -a https://authors.library.caltech.edu/rest -u XXXXX -p XXXXX

Beginning to process 1 EPrints entry.
Output will be written under directory "/tmp/eprints"
======================================================================
Getting record with id 85447
Creating /tmp/eprints/85447
Downloading https://authors.library.caltech.edu/85447/1/1-s2.0-S0164121218300517-main.pdf
Making bag out of /tmp/eprints/85447
Creating tarball /tmp/eprints/85447.tgz
======================================================================
Done. Wrote 1 EPrints record to /tmp/eprints/.
```

The following is a screen cast to give a sense for what it's like to run `eprints2bags`. Click on the following image:

<p align="center">
  <a href="https://asciinema.org/a/kUg8werG8YPobFKgPhsJnHwBi"><img width="80%" src="https://raw.githubusercontent.com/caltechlibrary/eprints2bags/main/.graphics/eprints2bags-asciinema.png" alt="Screencast of simple eprints2bags demo"></a>
</p>


### _Summary of command-line options_

The following table summarizes all the command line options available. (Note: on Windows computers, `/` must be used as the prefix character instead of `-`):

| Short&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;   | Long&nbsp;form&nbsp;opt&nbsp;&nbsp; | Meaning | Default |  |
|---------|-------------------|----------------------|---------|---|
| `-a`_A_ | `--api-url`_A_    | Use _A_ as the server's REST API URL | | ⚑ |
| `-b`_B_ | `--bag-action`_B_ | Do _B_ with each record directory | Bag and archive  | ✦ |
| `-c`_C_ | `--processes`_C_  | No. of processes during bag creation | &frac12; the number of CPUs | |
| `-e`_E_ | `--end-action`_E_ | Do _E_ with the entire set of records | Nothing | ✦ |
| `-i`_I_ | `--id-list`_I_    | Records to get (can be a file name) | Fetch all records from the server | |
| `-k`    | `--keep-going`    | Don't count missing records as an error | Stop if encounter missing record | |
| `-l`_L_ | `--lastmod`_L_    | Filter by last-modified date/time | Don't filter by date/time | |
| `-n`_N_ | `--name-base`_N_  | Prefix directory names with _N_ | Use record number only | |
| `-o`_O_ | `--output-dir`_O_ | Write outputs in the directory _O_ | Write in the current directory |  |
| `-q`    | `--quiet`         | Don't print info messages while working | Be chatty while working | |
| `-s`_S_ | `--status`_S_     | Filter by status(s) in _S_ | Don't filter by status | |
| `-u`_U_ | `--user`_U_       | User name for EPrints server login | |
| `-p`_P_ | `--password`_U_   | Password for EPrints proxy login | |
| `-t`_T_ | `--arch-type`_T_  | Use archive type _T_ | Uncompressed ZIP | ♢ |
| `-C`    | `--no-color`      | Don't color-code the output | Use colors in the terminal output | |
| `-K`    | `--no-keyring`    | Don't use a keyring/keychain | Store login info in keyring | |
| `-R`    | `--reset`         | Reset user login & password used | Reuse previous credentials |
| `-V`    | `--version`       | Print program version info and exit | Do other actions instead | |
| `-@`_OUT_ | `--debug`_OUT_    | Debugging mode; write trace to _OUT_ | Normal mode | ⚐ |

 ⚑ &nbsp; Required argument.<br>
✦ &nbsp; Possible values: `none`, `bag`, `bag-and-archive`.<br>
♢ &nbsp; Possible values: `uncompressed-zip`, `compressed-zip`, `uncompressed-tar`, `compressed-tar`.<br>
⚐ &nbsp; To write to the console, use the character `-` as the value of _OUT_; otherwise, _OUT_ must be the name of a file where the output should be written.

### Additional notes and considerations

Beware that some file systems have limitations on the number of subdirectories that can be created, which directly impacts how many record subdirectories can be created by this program.  `eprints2bags` attempts to guess the type of file system where the output is being written and warn the user if the number of records exceeds known maximums (e.g., 31,998 subdirectories for the [ext2](https://en.wikipedia.org/wiki/Ext2) and [ext3](https://en.wikipedia.org/wiki/Ext3) file systems in Linux), but its internal table does not include all possible file systems and it may not be able to warn users in all cases.  If you encounter file system limitations on the number of subdirectories that can be created, a simple solution is to manually create an intermediate level of subdirectories under the destination given to `-o`, then run `eprints2bags` multiple times, each time indicating a different subrange of records to the `-i` option and a different subdirectory to `-o`, such that the number of records written to each destination is below the file system's limit on total number of directories.

For maximum performance, the debug logging code that implements option `-@` can be skipped completely at run-time by running Python with optimization turn on.  One way to do this is to run eprints2bags using an invocation such as the following:

```
python -O -m eprints2bags ...other arguments...
```


⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/eprints2bags/issues) for this repository.


★ Do you like it?
------------------

If you like this software, don't forget to give this repo a star on GitHub to show your support!


♬ Contributing &mdash; info for developers
------------------------------------------

We would be happy to receive your help and participation with enhancing `eprints2bags`!  Please visit the [guidelines for contributing](CONTRIBUTING.md) for some tips on getting started.


❡ History
--------

In 2018, [Betsy Coles](https://github.com/betsycoles) wrote a [set of Perl scripts](https://github.com/caltechlibrary/eprints2dpn) and described a workflow for bagging contents from Caltech's EPrints-based [Caltech Collection of Open Digital Archives (CODA)](https://libguides.caltech.edu/CODA) server.  The original code is still available in this repository in the [historical](historical) subdirectory.  In late 2018, Mike Hucka sought to expand the functionality of the original tools and generalize them in anticipation of having to stop using DPN because on 2018-12-04, DPN announced they were shutting down. Thus was born _Eprints2bags_.


☺︎ Acknowledgments
-----------------------

The [vector artwork](https://thenounproject.com/search/?q=bag&i=1002779) of a bag used as a logo for this repository was created by [StoneHub](https://thenounproject.com/stonehub/) from the Noun Project.  It is licensed under the Creative Commons [CC-BY 3.0](https://creativecommons.org/licenses/by/3.0/) license.

We thank the following people for suggestions and ideas that led to improvements in `eprints2bags`: Robert Doiel, Tom Morrell, Tommy Keswick.

`eprints2bags` makes use of numerous open-source packages, without which it would have been effectively impossible to develop `eprints2bags` with the resources we had.  We want to acknowledge this debt.  In alphabetical order, the packages are:

* [bagit](https://github.com/LibraryOfCongress/bagit-python) &ndash; Python library for working with [BagIt](https://tools.ietf.org/html/draft-kunze-bagit-17) style packages
* [colorama](https://github.com/tartley/colorama) &ndash; makes ANSI escape character sequences work under MS Windows terminals
* [dateparser](https://pypi.org/project/dateparser/) &ndash; parse dates in almost any string format
* [humanize](https://github.com/jmoiron/humanize) &ndash; helps write large numbers in a more human-readable form
* [ipdb](https://github.com/gotcha/ipdb) &ndash; the IPython debugger
* [keyring](https://github.com/jaraco/keyring) &ndash; access the system keyring service from Python
* [lxml](https://lxml.de) &ndash; an XML parsing library for Python
* [plac](http://micheles.github.io/plac/) &ndash; a command line argument parser
* [psutil](https://github.com/giampaolo/psutil) &ndash; process and system utilities
* [requests](http://docs.python-requests.org) &ndash; an HTTP library for Python
* [setuptools](https://github.com/pypa/setuptools) &ndash; library for `setup.py`
* [termcolor](https://pypi.org/project/termcolor/) &ndash; ANSI color formatting for output in terminal
* [twine](https://github.com/pypa/twine/) &ndash; Twine is a utility for publishing Python packages on PyPI
* [urllib3](https://urllib3.readthedocs.io/en/latest/) &ndash; HTTP client library for Python
* [validators](https://github.com/kvesteri/validators) &ndash; data validation package for Python

☮︎ Copyright and license
---------------------

Copyright (C) 2019, Caltech.  This software is freely distributed under a BSD/MIT type license.  Please see the [LICENSE](LICENSE) file for more information.
    
<div align="center">
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src="https://raw.githubusercontent.com/caltechlibrary/eprints2bags/main/.graphics/caltech-round.png">
  </a>
</div>

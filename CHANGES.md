Change log for eprints2bags
===========================

Next
-----

* Renamed branch `master` to `main`.
* Slightly improved and updated some internal code.


Version 1.9.2
-------------

* **Critical bug fix**: in a version of Python after 3.5, the behavior of getting raw data via the [requests](http://docs.python-requests.org) package changed in a way that caused `eprints2bags` to write zero-length data files to disk.  This version changes internal code to avoid the problem that causes this.
* Report missing and skipped records separately at the end, instead of calling everything "missing".


Version 1.9.1
-------------

* Update installation instructions in README.md to explain how to install from PyPI, and make README file more compatible with displaying it on PyPI.
* Fix PyPI-related issues in `setup.cfg`.
* Fix configuration bug in `setup.py`.


Version 1.9.0
-------------

* Fixed issue #9: out-of-order id lists are ignored.
* Added fix by [Tom Morrell](https://github.com/tmorrell) to `files.py` for when output is in the current directory.
* Changed the debug option `-@` to accept an argument for where to send the debug output trace. The behavior change of `-@` is not backward compatible.
* Internally, package metadata is now stored in `setup.cfg`.  Also, there is no `eprints2bags/__version__.py` anymore, and instead, some special code in `eprints2bags/__init__.py` extracts package-level variables directly from the installation created by `pip`.
* Redesigned the icon for `eprints2bags` to tie into Eprints a little bit better.
* Changed Caltech logo used on the bottom of the README.md file.  The previous logo is only approved by Caltech for use in certain official contexts.
* Fixed various small errors in the README.md file.
* Released on PyPI.


Version 1.8.2
-------------

* Improved handling of network and server connectivity issues (fixes issue #6)


Version 1.8.1
-------------

* Significant performance improvement due to using multiple processes more efficiently


Version 1.8.0
-------------

* New feature: provide the option to create a final, single top-level bag out of all the output (option `-e`)
* New feature: use multiple processes for bag creation and provide option `-c` for adjusting the number
* New command-line options `-b`, `-c`, `-e` and `-t`
* Previous option `-b` renamed to `-n`, and `-m` to `-k`
* Option `-B` removed (because it's now subsumed by other options)
* Slightly changed (again) the comment block written to the ZIP archives
* Fixed some bugs
* Updated help strings and text in README

Version 1.7.0
-------------

* Added new `--status` command-line option
* Fixed comments in ZIP file to use correct BagIt format version
* Updated help strings and text in README


Version 1.6.0
-------------

* Added new `--lastmod` command-line option
* Fixed failure to parse combinations of ranges passed as arguments to `-i` option
* Slightly changed the comment block written to a zip archive to make it more specific
* Updated help strings and text in README


Version 1.5.0
-------------

* Now stores login & password on a per-server basis, instead of (as previously) a single login & password for all servers
* Accepts empty user names and passwords for EPrints servers that don't need them
* Fixed handling lack of `official_url` elements in EPrints records
* Changed how thumbnail images and other files are identified for a given record, by looking at the `<relation>` element to see if it is `isVolatileVersionOf`
* Make sure to write files in UTF-8 format regardless of whether the user's environment variables are set properly.  (Previously, having set `LC_ALL` to an unusual value would result in an error such as `'ascii' codec can't encode character '\u2019' in position 3540: ordinal not in range(128)`.)
* Refactor credentials-handling code and remove no-longer-needed `credentials.py`
* Other minor internal changes


Version 1.4.0
-------------

* Fixed an important network handling bug that could cause incomplete records to be saved
* Fixed bugs in handling network exceptions while downloading content from servers
* Improved detection of file system limitations
* Makes `-o` an optional argument
* Fixed a missing Python package import
* Renamed `CONDUCT.md` to [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) so that GitHub can find it
* Added [`CONTRIBUTING.md`](CONTRIBUTING.md),
* Updated the documentation
* Fixed some other minor bugs
* Minor internal code refactoring


Version 1.3.0
-------------

Eprints2bags now generates uncompressed [ZIP](https://www.loc.gov/preservation/digital/formats/fdd/fdd000354.shtml) archives of bags by default, instead of using compressed [tar](https://en.wikipedia.org/wiki/Tar_(computing)) format.  This was done in the belief that ZIP format is more widely supported and because compressed archive file contents may be more difficult to recover if the archive file becomes corrupted.  Also, the program `eprints2bags` now uses the run-time environment's keychain/keyring services to store the user name and password between runs, for convenience when running the program repeatedly.  Finally, some of the the command-line options have been changed.

Change log for eprints2bags
===========================

Version 1.7.0
-------------

* Add new `--status` command-line option
* Fix comments in ZIP file to use correct BagIt format version
* Update help strings and text in README


Version 1.6.0
-------------

* Add new `--lastmod` command-line option
* Fix failure to parse combinations of ranges passed as arguments to `-i` option
* Slightly change the comment block written to a zip archive to make it more specific
* Update help strings and text in README


Version 1.5.0
-------------

* Store login & password on a per-server basis, instead of (as previously) a single login & password for all servers
* Accept empty user names and passwords for EPrints servers that don't need them
* Fix handling lack of `official_url` elements in EPrints records
* Change how thumbnail images and other files are identified for a given record, by looking at the `<relation>` element to see if it is `isVolatileVersionOf`
* Make sure to write files in UTF-8 format regardless of whether the user's environment variables are set properly.  (Previously, having set `LC_ALL` to an unusual value would result in an error such as `'ascii' codec can't encode character '\u2019' in position 3540: ordinal not in range(128)`.)
* Refactor credentials-handling code and remove no-longer-needed `credentials.py`
* Other minor internal changes


Version 1.4.0
-------------

* Fix an important network handling bug that could cause incomplete records to be saved
* Fix bugs in handling network exceptions while downloading content from servers
* Improve detection of file system limitations
* Makes `-o` an optional argument
* Fix a missing Python package import
* Rename `CONDUCT.md` to [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) so that GitHub can find it
* Add [`CONTRIBUTING.md`](CONTRIBUTING.md),
* Update the documentation
* Fix some other minor bugs
* Minor internal code refactoring


Version 1.3.0
-------------

Eprints2bags now generates uncompressed [ZIP](https://www.loc.gov/preservation/digital/formats/fdd/fdd000354.shtml) archives of bags by default, instead of using compressed [tar](https://en.wikipedia.org/wiki/Tar_(computing)) format.  This was done in the belief that ZIP format is more widely supported and because compressed archive file contents may be more difficult to recover if the archive file becomes corrupted.  Also, the program `eprints2bags` now uses the run-time environment's keychain/keyring services to store the user name and password between runs, for convenience when running the program repeatedly.  Finally, some of the the command-line options have been changed.

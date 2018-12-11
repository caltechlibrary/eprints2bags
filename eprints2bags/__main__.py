'''
eprints2bags: download records from an EPrints server and bag them up

Materials in EPrints must be extracted before they can be moved to a
preservation system such as DPN or another long-term storage or dark archive.
The program eprints2bags encapsulates the processes needed to gather the
materials and bundle them up in BagIt bags.

Historical note
---------------

The original idea and some starting algorithms for this code came from the
eprints2dpn (https://github.com/caltechlibrary/eprints2dpn) collection of
Perl scripts written by Betsy Coles in early 2018.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library
Betsy Coles <betsycoles@gmail.com> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import bagit
from   collections import defaultdict
import lxml.etree as etree
import os
from   os import path
import plac
import requests
import shutil
import tarfile
from   time import sleep
from   timeit import default_timer as timer
import traceback

import eprints2bags
from   eprints2bags.constants import ON_WINDOWS, KEYRING
from   eprints2bags.credentials import service_credentials, password
from   eprints2bags.credentials import keyring_credentials, save_keyring_credentials
from   eprints2bags.debug import set_debug, log
from   eprints2bags.messages import msg, color, MessageHandler
from   eprints2bags.network import network_available, download_files
from   eprints2bags.files import readable, writable, make_dir
from   eprints2bags.files import make_tarball, verify_tarball
from   eprints2bags.eprints import *


# Main program.
# ......................................................................

@plac.annotations(
    api_url    = ('the URL for the REST API of your server',         'option', 'a'),
    base_name  = ('use base name "B" for subdirectory names',        'option', 'b'),
    delay      = ('wait time between fetches (default: 100 ms)',     'option', 'd'),
    fetch_list = ('read file "F" for list of records to get',        'option', 'f'),
    missing_ok = ('do not count missing records as an error',        'flag',   'm'),
    output_dir = ('write output to directory "O"',                   'option', 'o'),
    password   = ('EPrints server user password',                    'option', 'p'),
    user       = ('EPrints server user login name',                  'option', 'u'),
    quiet      = ('do not print info messages while working',        'flag',   'q'),
    no_bags    = ('do not create bags; just leave the content',      'flag',   'B'),
    no_color   = ('do not color-code terminal output (default: do)', 'flag',   'C'),
    debug      = ('turn on debugging',                               'flag',   'D'),
    no_keyring = ('do not use a keyring',                            'flag',   'K'),
    reset      = ('reset user and password used',                    'flag',   'R'),
    version    = ('print version info and exit',                     'flag',   'V'),
)

def main(api_url = 'A', base_name = 'B', delay = 100, fetch_list = 'F',
         missing_ok = False, output_dir = 'O', user = 'U', password = 'P',
         quiet = False, debug = False, no_bags = False, no_color = False,
         no_keyring = False, reset = False, version = False):
    '''eprints2bags bags up EPrints content as BagIt bags.

This program contacts an EPrints REST server whose network API is accessible
at the URL given by the command-line option -a (or /a on Windows).  A typical
EPrints server URL has the form "https://server.institution.edu/rest".

The EPrints records to be written will be limited to the list of EPrints
numbers found in the file given by the option -f (or /f on Windows).  If no
-f option is given, this program will download all the contents available at
the given EPrints server.  The value of -f can also be one or more integers
separated by commas (e.g., -f 54602,54604), or a range of numbers separated
by a dash (e.g., -f 1-100, which is interpreted as the list of numbers 1, 2,
..., 100 inclusive).  In those cases, the records written will be limited to
those numbered.

By default, if a record requested or implied by the arguments to -f is
missing from the EPrints server, this will count as an error and stop
execution of the program.  If the option -m (or /m on Windows) is given,
missing records will be ignored.

This program writes the output in the directory given by the command line
option -o (or /o on Windows).  If the directory does not exist, this program
will create it.  If the directory does exist, it will be overwritten with the
new content.  The result of running this program will be individual
directories underneath the directory given by the -o option, with each
subdirectory named according to the EPrints record number (e.g.,
/path/to/output/430, /path/to/output/431, ...).  If the -b option (/b on
Windows) is given, the subdirectory names are changed to have the form
"BASENAME-NUMBER" where BASENAME is the text string provided with the -b
option and the NUMBER is the EPrints number for a given entry.

Each directory will contain an EP3XML XML file and additional document
file(s) associated with the EPrints record in question.  Documents associated
with each record will be fetched over the network.  The list of documents for
each record is determined from XML file, in the <documents> element.  Certain
EPrints internal documents such as "indexcodes.txt" are ignored.

Downloading documents usually requires supplying a user login and password to
the EPrints server.  By default, this program uses the operating system's
keyring/keychain functionality to get a user name and password.  If the
information does not exist from a previous run of eprints2bags, it will query
the user interactively for the user name and password, and (unless the -K or
/K argument is given) store them in the user's keyring/keychain so that it
does not have to ask again in the future.  It is also possible to supply the
information directly on the command line using the -u and -p options (or /u
and /p on Windows), but this is discouraged because it is insecure on
multiuser computer systems.

To reset the user name and password (e.g., if a mistake was made the last time
and the wrong credentials were stored in the keyring/keychain system), add the
-R (or /R on Windows) command-line argument to a command.  The next time
eprints2bags runs, it will query for the user name and password again even
if an entry already exists in the keyring or keychain.

The final step of this program is to create BagIt bags from the contents of
the subdirectories created for each record, then tar up and gzip the bag
directory.  This is done by default, after the documents are downloaded for
each record, unless the -B option (/B on Windows) is given.  Note that
creating bags is a destructive operation: it replaces the individual
directories of each record with a restructured directory corresponding to the
BagIt format.

If the -B (/B on  Windows) is given, bags will not be created and the content
directories will be left in the output directory (the location given by the
-o or /o option).

This program will print messages as it works.  To reduce the number of messages
to warnings and errors, use the option -q (or /q on Windows).  The output will
be color-coded unless the -C option (or /C on Windows) is given; this option
can be helpful if the color control signals create problems for your terminal
emulator.

Beware that some file systems have limitations on the number of subdirectories
that can be created, which directly impacts how many record subdirectories
can be created by this program.  In particular, note that Linux ext2 and ext3
file systems are limited to 31,998 subdirectories.  This means you cannot
grab more than 32,000 entries at a time from an EPrints server.

It is also noteworthy that hitting a server for tens of thousands of records
and documents in rapid succession is likely to draw suspicion from server
administrators.  By default, this program inserts a small delay between
record fetches (adjustable using the -d command-line option), which may be
too short in some cases.  Setting the value to 0 is also possible, but might
get you blocked or banned from an institution's servers.
'''
    # Initial setup -----------------------------------------------------------

    keyring = not no_keyring   # Avoid double negative in code, for readability
    say = MessageHandler(not no_color, quiet)
    prefix = '/' if ON_WINDOWS else '-'
    hint = '(Hint: use {}h for help.)'.format(prefix)

    # Process arguments -------------------------------------------------------

    if debug:
        set_debug(True)
    if version:
        print_version()
        exit()
    if not network_available():
        exit(say.fatal_text('No network.'))

    if api_url == 'A':
        exit(say.fatal_text('Must provide an Eprints API URL. {}', hint))
    elif not api_url.startswith('http'):
        exit(say.fatal_text('Argument to {}a must be a full URL.', prefix))

    if base_name == 'B':
        name_prefix = ''
    else:
        name_prefix = base_name + '-'

    # Wanted is a list of strings, not of ints, to avoid repeated conversions.
    if ',' in fetch_list or fetch_list.isdigit():
        wanted = fetch_list.split(',')
    elif '-' in fetch_list and '.' not in fetch_list:
        range_list = fetch_list.split('-')
        # This makes the range 1-100 be 1, 2, ..., 100 instead of 1, 2, ..., 99
        wanted = [*map(str, range(int(range_list[0]), int(range_list[1]) + 1))]
    elif fetch_list != 'F':
        if not path.isabs(fetch_list):
            fetch_list = path.realpath(path.join(os.getcwd(), fetch_list))
        if not path.exists(fetch_list):
            exit(say.fatal_text('File not found: {}', fetch_list))
        if not readable(fetch_list):
            exit(say.fatal_text('File not readable: {}', fetch_list))
        with open(fetch_list, 'r', encoding = 'utf-8-sig') as file:
            if __debug__: log('Reading {}'.format(fetch_list))
            wanted = [id.strip() for id in file.readlines()]
    else:
        wanted = []

    if output_dir == 'O':
        exit(say.fatal_text('Must provide an output directory using the -o option'))
    if not path.isabs(output_dir):
        output_dir = path.realpath(path.join(os.getcwd(), output_dir))
    if path.isdir(output_dir):
        if not writable(output_dir):
            exit(say.fatal_text('Directory not writable: {}', output_dir))

    if user == 'U':
        user = None
    if password == 'P':
        password = None

    # Do the real work --------------------------------------------------------

    try:
        if not wanted:
            if __debug__: log('Fetching records list from {}'.format(api_url))
            wanted = eprints_records_list(api_url, user, password)
        if len(wanted) >= 31998:
            exit(say.fatal_text("Can't process more than 31,998 entries due to file system limitations."))

        if not user or not password or reset:
            user, password = login_credentials(user, password, keyring, reset)

        say.info('Beginning to process {} EPrints {}.', len(wanted),
                 'entries' if len(wanted) > 1 else 'entry')
        say.info('Output will be written under directory "{}"', output_dir)
        if not path.exists(output_dir):
            os.mkdir(output_dir)
            if __debug__: log('Created output directory {}', output_dir)

        if not quiet:
            say.msg('='*70, 'dark')
        count = 0
        missing = wanted.copy()
        for number in wanted:
            # Start by getting the full record in EP3 XML format.  A failure
            # here will either cause an exit or moving to the next record.
            try:
                say.msg('Getting record with id {}'.format(number), 'white')
                xml_element = eprints_xml(number, api_url, user, password)
            except NoContent:
                if missing_ok:
                    say.warn('Server has no content for {}', number)
                    continue
                else:
                    raise

            # Good so far.  Create the directory and write the XML out.
            record_dir = path.join(output_dir, name_prefix + str(number))
            say.info('Creating {}', record_dir)
            make_dir(record_dir)
            write_record(number, xml_element, name_prefix, record_dir)

            # Download any documents referenced in the XML record.
            associated_documents = eprints_documents(xml_element)
            download_files(associated_documents, user, password, record_dir, say)

            # Bag up, tar up, and gzip the directory by default.
            if not no_bags:
                say.info('Making bag out of {}', record_dir)
                bag = bagit.make_bag(record_dir,
                                     checksums = ["sha256", "sha512", "md5"])
                bag.validate()
                tar_file = record_dir + '.tgz'
                say.info('Creating tarball {}', tar_file)
                make_tarball(record_dir, tar_file)
                verify_tarball(tar_file)
                shutil.rmtree(record_dir)

            # Track what we've done so far.
            count += 1
            if wanted and number in wanted:
                missing.remove(number)
            if delay:
                sleep(delay/1000)

        if not quiet:
            say.msg('='*70, 'dark')
        say.info('Done. Wrote {} EPrints record{} to {}/.', count,
                 's' if count > 1 else '', output_dir)
        if len(missing) > 500:
            say.warn('More than 500 records requested with -f were not found')
        elif len(missing) > 0:
            say.warn('The following records were not found: '+ ', '.join(missing) + '.')
    except KeyboardInterrupt as err:
        exit(say.msg('Quitting.', 'error'))
    except CorruptedContent as err:
        exit(say.fatal_text(str(err)))
    except bagit.BagValidationError as err:
        exit(say.fatal_text('Bag validation failure: {}'.format(str(err))))
    except Exception as err:
        if debug:
            say.error('{}\n{}', str(err), traceback.format_exc())
            import pdb; pdb.set_trace()
        else:
            exit(say.error_text('{}', str(err)))


# If this is windows, we want the command-line args to use slash intead
# of hyphen.

if ON_WINDOWS:
    main.prefix_chars = '/'


# Helper functions.
# ......................................................................

def print_version():
    print('{} version {}'.format(eprints2bags.__title__, eprints2bags.__version__))
    print('Author: {}'.format(eprints2bags.__author__))
    print('URL: {}'.format(eprints2bags.__url__))
    print('License: {}'.format(eprints2bags.__license__))


def login_credentials(user, pswd, use_keyring, reset):
    if use_keyring and not reset:
        if __debug__: log('Getting credentials from keyring')
        tmp_user, tmp_pswd, _, _ = service_credentials(KEYRING, "EPrints server",
                                                       user, pswd)
    else:
        if not use_keyring:
            if __debug__: log('Keyring disabled')
        if reset:
            if __debug__: log('Reset invoked')
        tmp_user = input('EPrints server login: ')
        tmp_pswd = password('Password for "{}": '.format(tmp_user))
    if use_keyring:
        # Save the credentials if they're different.
        s_user, s_pswd, _, _ = keyring_credentials(KEYRING)
        if s_user != tmp_user or s_pswd != tmp_pswd:
            if __debug__: log('Saving credentials to keyring')
            save_keyring_credentials(KEYRING, tmp_user, tmp_pswd)
    return tmp_user, tmp_pswd


# Main entry point.
# ......................................................................
# The following allows users to invoke this using "python3 -m eprints2bags".

if __name__ == '__main__':
    plac.call(main)


# For Emacs users
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:

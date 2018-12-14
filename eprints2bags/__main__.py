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
from   humanize import intcomma
from   lxml import etree
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
from   eprints2bags.files import fs_type, KNOWN_SUBDIR_LIMITS
from   eprints2bags.files import create_archive, verify_archive, archive_extension
from   eprints2bags.eprints import *


# Constants.
# ......................................................................

_RECOGNIZED_ARCHIVE_FORMATS = ['none', 'compressed-zip', 'uncompressed-zip',
                               'compressed-tar', 'uncompressed-tar']
'''List of values recognized for the final archive file format.'''

_BAG_CHECKSUMS = ["sha256", "sha512", "md5"]
'''List of checksum types written with the BagIt bags.'''


# Main program.
# ......................................................................

@plac.annotations(
    api_url    = ('the URL for the REST API of the EPrints server',  'option', 'a'),
    base_name  = ('use base name "B" for subdirectory names',        'option', 'b'),
    final_fmt  = ('create single-file archive of bag in format "F"', 'option', 'f'),
    id_list    = ('list of records to get (can be a file name)',     'option', 'i'),
    missing_ok = ('do not count missing records as an error',        'flag',   'm'),
    output_dir = ('write output to directory "O"',                   'option', 'o'),
    password   = ('EPrints server user password',                    'option', 'p'),
    user       = ('EPrints server user login name',                  'option', 'u'),
    quiet      = ('do not print info messages while working',        'flag',   'q'),
    delay      = ('wait time between fetches (default: 100 ms)',     'option', 'y'),
    no_bags    = ('do not create bags; just leave the content',      'flag',   'B'),
    no_color   = ('do not color-code terminal output',               'flag',   'C'),
    no_keyring = ('do not use a keyring service',                    'flag',   'K'),
    reset_keys = ('reset user and password used',                    'flag',   'R'),
    version    = ('print version info and exit',                     'flag',   'V'),
    debug      = ('turn on debugging',                               'flag',   'Z'),
)

def main(api_url = 'A', base_name = 'B', final_fmt = 'F',  id_list = 'I',
         missing_ok = False, output_dir = 'O', user = 'U', password = 'P',
         quiet = False, delay = 100, no_bags = False, no_color = False,
         no_keyring = False, reset_keys = False, version = False, debug = False):
    '''eprints2bags bags up EPrints content as BagIt bags.

This program contacts an EPrints REST server whose network API is accessible
at the URL given by the command-line option -a (or /a on Windows).  A typical
EPrints server URL has the form "https://server.institution.edu/rest".

The EPrints records to be written will be limited to the list of EPrints
numbers found in the file given by the option -i (or /i on Windows).  If no
-i option is given, this program will download all the contents available at
the given EPrints server.  The value of -i can also be one or more integers
separated by commas (e.g., -i 54602,54604), or a range of numbers separated
by a dash (e.g., -i 1-100, which is interpreted as the list of numbers 1, 2,
..., 100 inclusive), or some combination thereof.  In those cases, the
records written will be limited to those numbered.

By default, if a record requested or implied by the arguments to -i is
missing from the EPrints server, this will count as an error and stop
execution of the program.  If the option -m (or /m on Windows) is given,
missing records will be ignored.

This program writes its output in subdirectories under the directory given by
the command-line option -o (or /o on Windows).  If the directory does not
exist, this program will create it.  If no -o is given, the current directory
where eprints2bags is running is used.  Whatever the destination is,
eprints2bags will create subdirectories in the destination, with each
subdirectory named according to the EPrints record number (e.g.,
/path/to/output/430, /path/to/output/431, /path/to/output/432, ...).  If the
-b option (/b on Windows) is given, the subdirectory names are changed to
have the form _BASENAME-NUMBER_ where _BASENAME_ is the text string provided
with the -b option and the _NUMBER_ is the EPrints number for a given entry
(meaning, /path/to/output/BASENAME-430, /path/to/output/BASENAME-431,
/path/to/output/BASENAME-432, ...).

Each directory will contain an EP3XML XML file and additional document
file(s) associated with the EPrints record in question.  Documents associated
with each record will be fetched over the network.  The list of documents for
each record is determined from XML file, in the <documents> element.  Certain
EPrints internal documents such as "indexcodes.txt" are ignored.

The records downloaded from EPrints will be placed in BagIt style packages
unless the -B option (/B on Windows) is given.  Note that creating bags is a
destructive operation: it replaces the individual directories of each record
with a restructured directory corresponding to the BagIt format.  If the -B
(/B on Windows) is given, bags will not be created and the content
directories will be left in the output directory (the location given by the
-o or /o option).

Each bag directory will also be put into a single-file archive by default.
The archive file format will be ZIP with compression turned off.  The option
-f (or /f on Windows) can be used to change the archive format.  If given the
value "none", the bags are not put into an archive file and are instead left
as-is.  Other possible values are: "compressed-zip", "uncompressed-zip",
"compressed-tar", and "uncompressed-tar".  The default is "uncompressed-zip"
(used if no -f option is given).  ZIP is the default because it is more widely
recognized and supported than tar format, and uncompressed ZIP is used because
file corruption is generally more damaging to a compressed archive than an
uncompressed one.  Since the main use case for eprints2bags is to archive
contents for long-term storage, avoiding compression seems safer.

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

To reset the user name and password (e.g., if a mistake was made the last
time and the wrong credentials were stored in the keyring/keychain system),
add the -R (or /R on Windows) command-line argument to a command.  When
`eprints2bags` is run with this option, it will query for the user name and
password again even if an entry already exists in the keyring or keychain.

This program will print messages as it works.  To reduce the number of messages
to warnings and errors, use the option -q (or /q on Windows).  The output will
be color-coded unless the -C option (or /C on Windows) is given; this option
can be helpful if the color control signals create problems for your terminal
emulator.

Beware that some file systems have limitations on the number of
subdirectories that can be created, which directly impacts how many record
subdirectories can be created by this program.  eprints2bags attempts to
guess the type of file system where the output is being written and warn the
user if the number of records exceeds known maximums (e.g., 31,998
subdirectories for the ext2 and ext3 file systems in Linux), but its internal
table does not include all possible file systems and it may not be able to
warn users in all cases.  If you encounter file system limitations on the
number of subdirectories that can be created, a simple solution is to
manually create an intermediate level of subdirectories under the destination
given to -o, then run eprints2bags multiple times, each time indicating a
different subrange of records to the -i option and a different subdirectory
to -o, such that the number of records written to each destination is below
the file system's limit on total number of directories.

It is also noteworthy that hitting a server for tens of thousands of records
and documents in rapid succession is likely to draw suspicion from server
administrators.  By default, this program inserts a small delay between
record fetches (adjustable using the -y command-line option), which may be
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

    # Wanted is a list of strings, not of ints, to avoid repeated conversions.
    if id_list == 'I':
        wanted = []
    elif ',' in id_list or id_list.isdigit():
        wanted = id_list.split(',')
    elif '-' in id_list and '.' not in id_list:
        range_list = id_list.split('-')
        # This makes the range 1-100 be 1, 2, ..., 100 instead of 1, 2, ..., 99
        wanted = [*map(str, range(int(range_list[0]), int(range_list[1]) + 1))]
    elif id_list != 'F':
        if not path.isabs(id_list):
            id_list = path.realpath(path.join(os.getcwd(), id_list))
        if not path.exists(id_list):
            exit(say.fatal_text('File not found: {}', id_list))
        if not readable(id_list):
            exit(say.fatal_text('File not readable: {}', id_list))
        with open(id_list, 'r', encoding = 'utf-8-sig') as file:
            if __debug__: log('Reading {}'.format(id_list))
            wanted = [id.strip() for id in file.readlines()]
    else:
        wanted = []

    if output_dir == 'O':
        output_dir = os.getcwd()
    if not path.isabs(output_dir):
        output_dir = path.realpath(path.join(os.getcwd(), output_dir))
    if path.isdir(output_dir):
        if not writable(output_dir):
            exit(say.fatal_text('Directory not writable: {}', output_dir))

    if user == 'U':
        user = None
    if password == 'P':
        password = None

    delay = int(delay)
    name_prefix = '' if base_name == 'B' else base_name + '-'
    archive_fmt = "uncompressed-zip" if final_fmt == 'F' else final_fmt.lower()
    if archive_fmt and archive_fmt not in _RECOGNIZED_ARCHIVE_FORMATS:
        exit(say.fatal_text('Value of {}f option not recognized. {}', prefix, hint))

    # Do the real work --------------------------------------------------------

    try:
        if not user or not password or reset_keys:
            user, password = login_credentials(user, password, keyring, reset_keys)

        if not wanted:
            if __debug__: log('Fetching records list from {}'.format(api_url))
            wanted = eprints_records_list(api_url, user, password)
        fs = fs_type(output_dir)
        if __debug__: log('Destination file system is {}', fs)
        if fs in KNOWN_SUBDIR_LIMITS and len(wanted) > KNOWN_SUBDIR_LIMITS[fs]:
            text = '{} is too many folders for the file system at "{}".'
            exit(say.fatal_text(text.format(intcomma(num_wanted), output_dir)))

        say.info('Beginning to process {} EPrints {}.', intcomma(len(wanted)),
                 'entries' if len(wanted) > 1 else 'entry')
        say.info('Output will be written under directory "{}"', output_dir)
        make_dir(output_dir)

        say.msg('='*70, 'dark')
        missing = wanted.copy()
        for number in wanted:
            # Start by getting the full record in EP3 XML format.  A failure
            # here will either cause an exit or moving to the next record.
            say.msg('Getting record with id {}'.format(number), 'white')
            xml = eprints_xml(number, api_url, user, password, missing_ok, say)
            if xml == None:
                continue

            # Good so far.  Create the directory and write the XML out.
            record_dir = path.join(output_dir, name_prefix + str(number))
            say.info('Creating {}', record_dir)
            make_dir(record_dir)
            write_record(number, xml, name_prefix, record_dir)

            # Download any documents referenced in the XML record.
            docs = eprints_documents(xml)
            download_files(docs, user, password, record_dir, missing_ok, say)

            # Bag up the directory by default.
            if not no_bags:
                say.info('Making bag out of {}', record_dir)
                bag = bagit.make_bag(record_dir, checksums = _BAG_CHECKSUMS)
                update_bag_info(bag, xml)
                bag.save()
                if __debug__: log('Verifying bag {}', bag.path)
                bag.validate()

                # Create single-file archives of the bags by default.
                if archive_fmt != 'none':
                    dest = record_dir + archive_extension(archive_fmt)
                    say.info('Creating archive file {}', dest)
                    create_archive(dest, archive_fmt, record_dir, file_comments(bag))
                    if __debug__: log('Verifying archive file {}', dest)
                    verify_archive(dest, archive_fmt)
                    if __debug__: log('Deleting directory {}', record_dir)
                    shutil.rmtree(record_dir)

            # Track what we've done so far.
            if wanted and number in wanted:
                missing.remove(number)
            sleep(delay/1000)

        say.msg('='*70, 'dark')
        count = len(wanted) - len(missing)
        say.info('Done. Wrote {} EPrints record{} to {}/.', intcomma(count),
                 's' if count > 1 else '', output_dir)
        if len(missing) > 0:
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


def update_bag_info(bag, xml):
    official_url = eprints_official_url(xml)
    bag.info['Internal-Sender-Identifier'] = eprints_record_id(xml)
    bag.info['External-Identifier'] = official_url
    bag.info['External-Description'] = 'Archive of EPrints record and document files'


def file_comments(bag):
    text = '~ '*35
    text += '\n'
    text += 'About this archive file:\n'
    text += '\n'
    text += 'This is an archive of a file directory organized in BagIt v1.0 format.\n'
    text += 'The bag contains the contents from the EPrints record located at\n'
    text += bag.info['External-Identifier']
    text += '\n\n'
    text += 'The software used to create this archive file was:\n'
    text += '{} version {} <{}>'.format(
        eprints2bags.__title__, eprints2bags.__version__, eprints2bags.__url__)
    text += '\n\n'
    text += 'The following is the metadata contained in bag-info.txt:\n'
    text += '\n'.join('{}: {}'.format(k, v) for k, v in sorted(bag.info.items()))
    text += '\n'
    text += '~ '*35
    text += '\n'
    return text


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

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

Copyright (c) 2019 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import bagit
from   collections import defaultdict
import getpass
from   humanize import intcomma
import keyring
from   lxml import etree
import os
from   os import path
import plac
import requests
import shutil
import sys
import tarfile
from   time import sleep
from   timeit import default_timer as timer

if sys.platform.startswith('win'):
    import keyring.backends
    from keyring.backends.Windows import WinVaultKeyring

import eprints2bags
from   eprints2bags import print_version
from   eprints2bags.constants import ON_WINDOWS, KEYRING_PREFIX
from   eprints2bags.data_helpers import flatten, expand_range, parse_datetime
from   eprints2bags.debug import set_debug, log
from   eprints2bags.messages import msg, color, MessageHandler
from   eprints2bags.network import network_available, download_files, url_host
from   eprints2bags.files import readable, writable, make_dir
from   eprints2bags.files import fs_type, KNOWN_SUBDIR_LIMITS
from   eprints2bags.files import create_archive, verify_archive, archive_extension
from   eprints2bags.processes import available_cpus
from   eprints2bags.eprints import *


# Constants.
# ......................................................................

_RECOGNIZED_ACTIONS = ['none', 'bag', 'bag-and-archive', 'bag+archive']

_RECOGNIZED_ARCHIVE_TYPES = ['compressed-zip', 'uncompressed-zip',
                             'compressed-tar', 'uncompressed-tar']
'''List of values recognized for the final archive file format.'''

_BAG_CHECKSUMS = ["sha256", "sha512", "md5"]
'''List of checksum types written with the BagIt bags.'''

_LASTMOD_PRINT_FORMAT = '%b %d %Y %H:%M:%S %Z'
'''Format in which lastmod date is printed back to the user. The value is used
with datetime.strftime().'''


# Main program.
# ......................................................................

@plac.annotations(
    api_url    = ('the URL for the REST API of the EPrints server',         'option', 'a'),
    bag_action = ('bag, bag & archive, or none? (default: bag & archive)',  'option', 'b'),
    processes  = ('num. processes to use when bagging (default: #cores/2)', 'option', 'c'),
    end_action = ('final action over whole set of records (default: none)', 'option', 'e'),
    id_list    = ('list of records to get (can be a file)',                 'option', 'i'),
    keep_going = ('do not stop if missing records or errors encountered',   'flag',   'k'),
    lastmod    = ('only get records modified after given date/time',        'option', 'l'),
    name_base  = ('prefix names with "N-" when naming record directories',  'option', 'n'),
    output_dir = ('write output to directory "O"',                          'option', 'o'),
    quiet      = ('do not print informational messages while working',      'flag',   'q'),
    status     = ('only get records whose status is in the list "S"',       'option', 's'),
    user       = ('EPrints server user login name "U"',                     'option', 'u'),
    password   = ('EPrints server user password "P"',                       'option', 'p'),
    arch_type  = ('use archive type "T" (default: "uncompressed-zip")',     'option', 't'),
    delay      = ('wait time between fetches (default: 100 ms)',            'option', 'y'),
    no_color   = ('do not color-code terminal output',                      'flag',   'C'),
    no_keyring = ('do not store credentials in a keyring service',          'flag',   'K'),
    reset_keys = ('reset user and password used',                           'flag',   'R'),
    version    = ('print version info and exit',                            'flag',   'V'),
    debug      = ('write detailed trace to "OUT" ("-" means console)',      'option', '@'),
)

def main(api_url = 'A', bag_action = 'B', processes = 'C', end_action = 'E',
         id_list = 'I', keep_going = False, lastmod = 'L', name_base = 'N',
         output_dir = 'O', quiet = False, status = 'S', user = 'U',
         password = 'P', arch_type = 'T', delay = 100, no_color = False,
         no_keyring = False, reset_keys = False, version = False, debug = 'OUT'):
    '''eprints2bags bags up EPrints content as BagIt bags.

This program contacts an EPrints REST server whose network API is accessible
at the URL given by the command-line option -a (or /a on Windows).  A typical
EPrints server URL has the form "https://server.institution.edu/rest".  This
program will automatically add "/eprint" to the URL path, so omit that part
of the URL in the value given to -a.

Specifying which records to get
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The EPrints records to be written will be limited to the list of EPrints
numbers found in the file given by the option -i (or /i on Windows).  If no
-i option is given, this program will download all the contents available at
the given EPrints server.  The value of -i can also be one or more integers
separated by commas (e.g., -i 54602,54604), or a range of numbers separated
by a dash (e.g., -i 1-100, which is interpreted as the list of numbers 1, 2,
..., 100 inclusive), or some combination thereof.  In those cases, the
records written will be limited to those numbered.

If the -l option (or /l on Windows) is given, the records will be additionally
filtered to return only those whose last-modified date/time stamp is no older
than the given date/time description.  Valid descriptors are those accepted
by the Python dateparser library.  Make sure to enclose descriptions within
single or double quotes.  Examples:

  eprints2bags -l "2 weeks ago" -a ....
  eprints2bags -l "2014-08-29"  -a ....
  eprints2bags -l "12 Dec 2014" -a ....
  eprints2bags -l "July 4, 2013" -a ....

If the -s option (or /s on Windows) is given, the records will also be filtered
to include only those whose eprint_status element value is one of the listed
status codes.  Comparisons are done in a case-insensitive manner.  Putting a
caret character ("^") in front of the status (or status list) negates the
sense, so that eprints2bags will only keep those records whose eprint_status
value is *not* among those given.  Examples:

  eprints2bags -s archive -a ...
  eprints2bags -s ^inbox,buffer,deletion -a ...

Both lastmod and status filering are done after the -i argument is processed.

By default, if an error occurs when requesting a record from the EPrints
server, it stops execution of eprints2bags.  Common causes of errors include
missing records implied by the arguments to -i, missing files associated with
a given record, and files inaccessible due to permissions errors.  If the
option -k (or /k on Windows) is given, eprints2bags will attempt to keep going
upon encountering missing records, or missing files within records, or similar
errors.  Option -k is particularly useful when giving a range of numbers with
the -i option, as it is common for EPrints records to be updated or deleted and
gaps to be left in the numbering.  (Running without -i will skip over gaps in
the numbering because the available record numbers will be obtained directly
from the server, which is unlike the user providing a list of record numbers
that may or may not exist on the server.  However, even without -i, errors may
still result from permissions errors or other causes.)

Specifying what to do with the output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This program writes its output in subdirectories under the directory given by
the command-line option -o (or /o on Windows).  If the directory does not
exist, this program will create it.  If no -o is given, the current directory
where eprints2bags is running is used.  Whatever the destination is,
eprints2bags will create subdirectories in the destination, with each
subdirectory named according to the EPrints record number (e.g.,
/path/to/output/43, /path/to/output/44, /path/to/output/45, ...).  If the
-n option (/n on Windows) is given, the subdirectory names are changed to
have the form NAME-NUMBER_ where NAME is the text string provided to the -n
option and the NUMBER is the EPrints number for a given entry (meaning,
/path/to/output/NAME-43, /path/to/output/NAME-44, /path/to/output/NAME-45, ...).

Each directory will contain an EP3XML XML file and additional document
file(s) associated with the EPrints record in question.  Documents associated
with each record will be fetched over the network.  The list of documents for
each record is determined from XML file, in the <documents> element.  Certain
EPrints internal documents such as "indexcodes.txt" and preview images
will be ignored.

Each record downloaded from EPrints will be placed in a BagIt style directory
and each bag will also be put into a single-file archive by default.  The
default archive file format is ZIP with compression turned off (see next
paragraph).  Option -b (/b on Windows) can be used to change this behavior.
This option takes a keyword value; possible values are "none", "bag" and
"bag-and-archive", with the last being the default.  Value "none" will cause
eprints2bags to leave the downloaded record content in individual directories
without bagging or archiving, and value "bag" will cause eprints2bags to
create BagIt bags but not single-file archives from the results.  The content
directories will be left in the output directory (the location given by the
-o or /o option).  Note that creating bags is a destructive operation: it
replaces the individual directories of each record with a restructured
directory corresponding to the BagIt format.

The type of archive made when "bag-and-archive" mode is used for the -b
option can be changed using the option -t (or /t on Windows).  The possible
values are: "compressed-zip", "uncompressed-zip", "compressed-tar", and
"uncompressed-tar".  As mentioned above, the default is "uncompressed-zip"
(used if no -t option is given).  ZIP is the default because it is more
widely recognized and supported than tar format, and uncompressed ZIP is used
because file corruption is generally more damaging to a compressed archive
than an uncompressed one.  Since the main use case for eprints2bags is to
archive contents for long-term storage, avoiding compression seems safer.

Finally, the overall collection of EPrints records (whether the records are
bagged and archived, or just bagged, or left as-is) can optionally be itself
put into a bag and/or put in a ZIP archive.  This behavior can be changed with
the option -e (/e on Windows).  Like -b, this option takes the possible values
"none", "bag", and "bag-and-archive".  The default is "none".  If the value
"bag" is used, a top-level bag containing the individual EPrints bags is
created out of the output directory (the location given by the -o option);
if the value "bag-and-archive" is used, the bag is also put into a single-file
archive.  (In other words, the result will be a ZIP archive of a bag whose
data directory contains other ZIP archives of bags.)  For safety, eprints2bags
will refuse to do "bag" or "bag-and-archive" unless a separate output directory
is given via the -o option; otherwise, this would restructure the current
directory where eprints2bags is running -- with potentially unexpected or even
catastrophic results.  (Imagine if the current directory were the user's home
directory!)

The use of separate options for the different stages provides some flexibility
in choosing the final output.  For example,

  eprints2bags  --bag-action  none  --end-action  bag-and-archive

will create a ZIP archive containing a single bag directory whose `data/`
subdirectory contains the set of (unbagged) EPrints records retrieved by
`eprints2bags` from the server.

Server credentials
~~~~~~~~~~~~~~~~~~

Downloading documents usually requires supplying a user login and password to
the EPrints server.  By default, this program uses the operating system's
keyring/keychain functionality to get a user name and password.  If the
information does not exist from a previous run of eprints2bags, it will query
the user interactively for the user name and password, and (unless the -K or
/K argument is given) store them in the user's keyring/keychain so that it
does not have to ask again in the future.  It is also possible to supply the
information directly on the command line using the -u and -p options (or /u
and /p on Windows), but this is discouraged because it is insecure on
multiuser computer systems.  If a given EPrints server does not require a user
name and password, do not use -u or -p and leave the values blank when
prompted for them by eprints2bags.  (Empty user name and password are allowed
values.)

To reset the user name and password (e.g., if a mistake was made the last
time and the wrong credentials were stored in the keyring/keychain system),
add the -R (or /R on Windows) command-line argument to a command.  When
eprints2bags is run with this option, it will query for the user name and
password again even if an entry already exists in the keyring or keychain.

Other command-line arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generating checksum values can be a time-consuming operation for large bags.
By default, during the bagging step, eprints2bags will use a number of
processes equal to one-half of the available CPUs on the computer.  The number
of processes can be changed using the option -c (or /c on Windows).

eprints2bags will print messages as it works.  To reduce the number of
messages to warnings and errors, use the option -q (or /q on Windows).  Also,
output is color-coded by default unless the -C option (or /C on Windows) is
given; this option can be helpful if the color control signals create
problems for your terminal emulator.

If given the -@ argument (/@ on Windows), this program will output a detailed
trace of what it is doing, and will also drop into a debugger upon the
occurrence of any errors.  The debug trace will be written to the given
destination, which can be a dash character (-) to indicate console output, or
a file path.

If given the -V option (/V on Windows), this program will print the version
and other information, and exit without doing anything else.

Additional notes
~~~~~~~~~~~~~~~~

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

Command-line options summary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
    # Initial setup -----------------------------------------------------------

    use_keyring = not no_keyring   # Avoid double negative, for readability.
    debugging = debug != 'OUT'
    say = MessageHandler(not no_color, quiet)
    prefix = '/' if ON_WINDOWS else '-'
    hint = '(Hint: use {}h for help.)'.format(prefix)

    # Process arguments -------------------------------------------------------

    if debugging:
        set_debug(True, debug)
        import faulthandler
        faulthandler.enable()
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
    else:
        wanted = list(parsed_id_list(id_list, say))

    if lastmod == 'L':
        lastmod = None
    else:
        try:
            lastmod = parse_datetime(lastmod)
            lastmod_str = lastmod.strftime(_LASTMOD_PRINT_FORMAT)
            if __debug__: log('Parsed lastmod as {}', lastmod_str)
        except Exception as ex:
            exit(say.fatal_text('Unable to parse lastmod value: {}', str(ex)))

    given_output_dir = not (output_dir == 'O')
    if output_dir == 'O':
        output_dir = os.getcwd()
    if not path.isabs(output_dir):
        output_dir = path.realpath(path.join(os.getcwd(), output_dir))
    if path.isdir(output_dir):
        if not writable(output_dir):
            exit(say.fatal_text('Directory not writable: {}', output_dir))

    bag_action = 'bag-and-archive' if bag_action == 'B' else bag_action.lower()
    if bag_action not in _RECOGNIZED_ACTIONS:
        exit(say.fatal_text('Value of {}b option not recognized. {}', prefix, hint))

    end_action = 'none' if end_action == 'E' else end_action.lower()
    if end_action not in _RECOGNIZED_ACTIONS:
        exit(say.fatal_text('Value of {}b option not recognized. {}', prefix, hint))
    if end_action != "none" and not given_output_dir:
        exit(say.fatal_text('Please specify an output directory when using -e "{}"', end_action))

    archive_fmt = 'uncompressed-zip' if arch_type == 'T' else arch_type.lower()
    if archive_fmt not in _RECOGNIZED_ARCHIVE_TYPES:
        exit(say.fatal_text('Value of {}t option not recognized. {}', prefix, hint))

    status = None if status == 'S' else status.split(',')
    status_negation = (status and status[0].startswith('^'))
    if status_negation:                 # Remove the '^' if it's there.
        status[0] = status[0][1:]

    delay = int(delay)
    procs = int(max(1, available_cpus()/2 if processes == 'C' else int(processes)))
    user = None if user == 'U' else user
    password = None if password == 'P' else password
    prefix = '' if name_base == 'N' else name_base + '-'

    # Do the real work --------------------------------------------------------

    try:
        if not user or not password:
            user, password = credentials(api_url, user, password, use_keyring, reset_keys)
        if __debug__: log('Testing given server URL')
        raw_list = eprints_raw_list(api_url, user, password)
        if raw_list == None:
            text = 'Did not get an EPrints server response from "{}"'.format(api_url)
            exit(say.fatal_text(text))
        if not wanted:
            say.info('Fetching records list from {}', api_url)
            wanted = eprints_records_list(raw_list)
        fs = fs_type(output_dir)
        if __debug__: log('Destination file system is {}', fs)
        if fs in KNOWN_SUBDIR_LIMITS and len(wanted) > KNOWN_SUBDIR_LIMITS[fs]:
            text = '{} is too many folders for the file system at "{}".'
            exit(say.fatal_text(text.format(intcomma(num_wanted), output_dir)))

        say.info('Beginning to process {} EPrints {}', intcomma(len(wanted)),
                 'entries' if len(wanted) > 1 else 'entry')
        if lastmod:
            say.info('Will only keep records modified after {}', lastmod_str)
        if status:
            say.info('Will only keep records {} status {}',
                     'without' if status_negation else 'with',
                     fmt_statuses(status, status_negation))
        say.info('Output will be written under directory "{}"', output_dir)
        make_dir(output_dir)

        say.msg('='*70, 'dark')
        missing = wanted.copy()
        for number in wanted:
            # Start by getting the full record in EP3 XML format.  A failure
            # here will either cause an exit or moving to the next record.
            say.msg('Getting record with id {}'.format(number), 'white')
            xml = eprints_xml(number, api_url, user, password, keep_going, say)
            if xml == None:
                continue
            if lastmod and eprints_lastmod(xml) < lastmod:
                say.info("{} hasn't been modified since {} -- skipping",
                         number, lastmod_str)
                continue
            if status and ((not status_negation and eprints_status(xml) not in status)
                           or (status_negation and eprints_status(xml) in status)):
                say.info('{} has status "{}" -- skipping', number, eprints_status(xml))
                continue

            # Good so far.  Create the directory and write the XML out.
            record_dir = path.join(output_dir, prefix + str(number))
            say.info('Creating {}', record_dir)
            make_dir(record_dir)
            write_record(number, xml, prefix, record_dir)

            # Download any documents referenced in the XML record.
            docs = eprints_documents(xml)
            download_files(docs, user, password, record_dir, keep_going, say)

            # Bag it and archive it, depending on user choice.
            bag_and_archive(record_dir, bag_action, archive_fmt, procs, xml, api_url, say)

            if wanted and number in wanted:
                missing.remove(number)
            sleep(delay/1000)

        say.msg('='*70, 'dark')
        count = len(wanted) - len(missing)
        say.info('Wrote {} EPrints record{} to {}/.', intcomma(count),
                 's' if count > 1 else '', output_dir)
        if len(missing) > 0:
            say.warn('The following records were not found: '+ ', '.join(missing) + '.')

        # Bag the whole result and archive it, depending on user choice.
        bag_and_archive(output_dir, end_action, archive_fmt, procs, None, api_url, say)

    except KeyboardInterrupt as ex:
        exit(say.msg('Quitting.', 'error'))
    except CorruptedContent as ex:
        exit(say.fatal_text(str(ex)))
    except bagit.BagValidationError as ex:
        exit(say.fatal_text('Bag validation failure: {}'.format(str(ex))))
    except Exception as ex:
        import traceback
        if debugging:
            say.error('{}\n{}', str(ex), traceback.format_exc())
            import pdb; pdb.set_trace()
        else:
            exit(say.error_text('Fatal error: {}', str(ex)))

# If this is windows, we want the command-line args to use slash intead
# of hyphen.

if ON_WINDOWS:
    main.prefix_chars = '/'


# Helper functions.
# ......................................................................

def parsed_id_list(id_list, say):
    # If it's a single digit, asssume it's not a file and return the number.
    if id_list.isdigit():
        return [id_list]

    # Things get trickier because anything else could be (however improbably)
    # a file name.  So use a process of elimination: try to see if a file by
    # that name exists, and if it doesn't, parse the argument as numbers.
    candidate = id_list
    if not path.isabs(candidate):
        candidate = path.realpath(path.join(os.getcwd(), candidate))
    if path.exists(candidate):
        if not readable(candidate):
            exit(say.fatal_text('File not readable: {}', candidate))
        with open(candidate, 'r', encoding = 'utf-8-sig') as file:
            if __debug__: log('Reading {}'.format(candidate))
            return [id.strip() for id in file.readlines()]

    # Didn't find a file.  Try to parse as multiple numbers.
    if ',' not in id_list and '-' not in id_list:
        exit(say.fatal_text('Unable to understand list of record identifiers'))
    return flatten(expand_range(x) for x in id_list.split(','))


def credentials(api_url, user, pswd, use_keyring, reset = False):
    '''Returns stored credentials for the given combination of host and user,
    or asks the user for new credentials if none are stored or reset is True.
    Empty user names and passwords are handled too.'''
    host = url_host(api_url)
    ringname = KEYRING_PREFIX + host
    if __debug__: log('Ring name: {}', ringname)
    NONE = '__EPRINTS2BAGS__NONE__'
    cur_user, cur_pswd = None, None
    if use_keyring and not reset:
        # This hack stores the user name as the "password" for a fake user 'user'
        cur_user = user or keyring.get_password(ringname, 'user')
        if user or (cur_user and cur_user != NONE):
            cur_pswd = pswd or keyring.get_password(ringname, user or cur_user)
        elif cur_user == NONE:
            cur_pswd = NONE
            if __debug__: log('Using empty user and password for {}', host)
    if reset or not cur_user:
        cur_user = input('User name for {}: '.format(host)) or NONE
    if reset or not cur_pswd:
        cur_pswd = password('Password for {}: '.format(host)) or NONE
    if use_keyring:
        if __debug__: log('Saving credentials to keyring')
        keyring.set_password(ringname, 'user', cur_user)
        keyring.set_password(ringname, cur_user, cur_pswd)
    return (None if cur_user == NONE else cur_user,
            None if cur_pswd == NONE else cur_pswd)


def password(prompt):
    # If it's a tty, use the version that doesn't echo the password.
    if sys.stdin.isatty():
        return getpass.getpass(prompt)
    else:
        sys.stdout.write(prompt)
        sys.stdout.flush()
        return sys.stdin.readline().rstrip()


def bag_and_archive(directory, action, archive_fmt, processes, xml, url, say):
    # If xml != None, we're dealing with a record, else the top-level directory.
    if action != 'none':
        say.info('Making bag out of {}', directory)
        # Don't use large # of processes b/c creating the process pool is
        # expensive.  If procs = 32 and most of our records have only 1-2
        # files, make_bag() will still create a pool of 32 each time.  The
        # following tries to balance things out for the most common case.
        # Note: this uses listdir to avoid walking down the directory tree,
        # but if a given entry is the root of a large subdirectory, then this
        # may fail to use multiple processes when it would be good to do so.
        procs = 1 if len(os.listdir(directory)) < processes else processes
        bag = bagit.make_bag(directory, checksums = _BAG_CHECKSUMS, processes = procs)
        if xml != None:
            # The official_url field is not always present in the record.
            # Try to get it, and default to using the eprints record id.
            official_url = eprints_official_url(xml)
            record_id = eprints_record_id(xml)
            extern_id = official_url if official_url else record_id
            bag.info['Internal-Sender-Identifier'] = record_id
            bag.info['External-Identifier'] = extern_id
            bag.info['External-Description'] = 'Single EPrints record and associated document files'
        else:
            # Case: the overall bag for the whole directory
            bag.info['External-Identifier'] = url
            bag.info['External-Description'] = 'Collection of EPrints records and their associated document files'
        bag.save()
        if __debug__: log('Verifying bag {}', bag.path)
        bag.validate()

        if action == 'bag-and-archive':
            archive_file = directory + archive_extension(archive_fmt)
            say.info('Making archive file {}', archive_file)
            comments = file_comments(bag) if xml != None else dir_comments(bag, url)
            create_archive(archive_file, archive_fmt, directory, comments)
            if __debug__: log('Verifying archive file {}', archive_file)
            verify_archive(archive_file, archive_fmt)
            if __debug__: log('Deleting directory {}', directory)
            shutil.rmtree(directory)


def file_comments(bag):
    text  = '~ '*35
    text += '\n'
    text += 'About this ZIP archive file:\n'
    text += '\n'
    text += 'This archive contains a directory of files organized in BagIt v{} format.\n'.format(bag.version)
    text += 'The data files in the bag are the contents of the EPrints record located at\n'
    text += bag.info['External-Identifier']
    text += '\n'
    text += software_comments()
    text += '\n'
    text += bag_comments(bag)
    text += '\n'
    text += '~ '*35
    text += '\n'
    return text


def dir_comments(bag, url):
    text  = '~ '*35
    text += '\n'
    text += 'About this ZIP archive file:\n'
    text += '\n'
    text += 'This archive contains a directory of files organized in BagIt v{} format.\n'.format(bag.version)
    text += 'The data files are the contents of EPrints records obtained from\n'
    text += url
    text += '\n'
    text += software_comments()
    text += '\n'
    text += bag_comments(bag)
    text += '\n'
    text += '~ '*35
    text += '\n'
    return text


def software_comments():
    text  = '\n'
    text += 'The software used to create this archive file was:\n'
    text += '{} version {} <{}>'.format(
        __package__, eprints2bags.__version__, eprints2bags.__url__)
    return text


def bag_comments(bag):
    text  = '\n'
    text += 'The following is the metadata contained in bag-info.txt:\n'
    text += '\n'.join('{}: {}'.format(k, v) for k, v in sorted(bag.info.items()))
    return text


def fmt_statuses(status_list, negated):
    as_list = ['"' + x + '"' for x in status_list]
    if len(as_list) > 1:
        and_or = ' or ' if negated else ' and '
        return ', '.join(as_list[:-1]) + and_or + as_list[-1]
    else:
        return as_list[0]


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

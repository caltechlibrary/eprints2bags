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
from   eprints2bags.constants import ON_WINDOWS
from   eprints2bags.debug import log
from   eprints2bags.messages import msg, color, MessageHandler
from   eprints2bags.network import network_available, download_files
from   eprints2bags.files import readable, writable, make_dir, make_tarball
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
    version    = ('print version info and exit',                     'flag',   'V'),
)

def main(api_url = 'A', base_name = 'B', delay = 100, fetch_list = 'F',
         missing_ok = False, output_dir = 'O', user = 'U', password = 'P',
         quiet = False, debug = False, no_bags = False, no_color = False,
         version = False):
    '''eprints2bags bags up EPrints content as BagIt bags.

This program contacts an EPrints REST server whose network API is accessible
at the URL given by the command-line option -a (or /a on Windows).  A typical
EPrints server URL has the form "https://server.institution.edu/rest".

The EPrints records to be written will be limited to the list of eprint
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

Downloading some documents may require supplying a user login and password to
the EPrints server.  These can be supplied using the command-line arguments
-u and -p, respectively (/u and /p on Windows).

The final step of this program is to create BagIt bags from the contents of
the subdirectories created for each record, then tar up and gzip the bag
directory.  This is done by default, after the documents are downloaded for
each record, unless the -B option (/B on Windows) is given.  Note that
creating bags is a destructive operation: it replaces the individual
directories of each record with a restructured directory corresponding to the
BagIt format.

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

        say.info('Beginning to process {} EPrints entries.', len(wanted))
        say.info('Output will be written under directory "{}"', output_dir)
        if not path.exists(output_dir):
            os.mkdir(output_dir)
            if __debug__: log('Created output directory {}', output_dir)

        count = 0
        missing = wanted.copy()
        say.msg('='*70, 'dark')
        for number in wanted:
            try:
                if __debug__: log('Fetching XML for {}'.format(number))
                xml_element = eprints_xml(number, api_url, user, password)
            except NoContent:
                if missing_ok:
                    continue
                else:
                    raise
            # Create the output subdirectory and write the DC and XML output.
            record_dir = path.join(output_dir, name_prefix + str(number))
            say.msg('Creating {}'.format(record_dir), 'white')
            make_dir(record_dir)
            write_record(number, xml_element, name_prefix, record_dir)
            # Download any documents referenced in the XML record.
            associated_documents = eprints_documents(xml_element)
            download_files(associated_documents, user, password, record_dir, say)
            # Bag up, tar up, and gzip the directory by default.
            if not no_bags:
                say.info('Making bag out of {}', record_dir)
                bagit.make_bag(record_dir, checksums = ["sha256", "sha512", "md5"])
                tar_file = record_dir + '.tgz'
                say.info('Creating {}', tar_file)
                make_tarball(record_dir, tar_file)
                shutil.rmtree(record_dir)
            # Track what we've done so far.
            count += 1
            if wanted and number in wanted:
                missing.remove(number)
            if delay:
                sleep(delay/1000)
    except KeyboardInterrupt as err:
        exit(say.fatal_text('Quitting.'))
    except Exception as err:
        if debug:
            import pdb; pdb.set_trace()
        say.error('{}\n{}', str(err), traceback.format_exc())

    say.msg('='*70, 'dark')
    say.info('Done. Wrote {} EPrints records to {}/.', count, output_dir)
    if len(missing) > 0:
        if len(missing) > 500:
            say.warn('More than 500 records requested with -f were not found')
        else:
            say.warn('The following records were not found: '+ ', '.join(missing) + '.')


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

'''
eprints2bag: download records from CODA bag them up

Materials in EPrints must be extracted before they can be moved to a
preservation system such as DPN or another long-term storage or dark archive.
_Eprints2bag_ encapsulates the processes needed to gather the materials and
bundle them up in BagIt bags.  You indicate which records from CODA you want
(based on record numbers), and it will download the content and bag it up.

Historical note
---------------

Much of the original algorithms and ideas for this code came from the
eprints2bag (https://github.com/caltechlibrary/eprints2bag) collection of
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
import traceback

import eprints2bag
from   eprints2bag.constants import ON_WINDOWS
from   eprints2bag.network import network_available, download_files
from   eprints2bag.files import readable, writable, make_dir, make_tarball
from   eprints2bag.eprints import *


# Main program.
# ......................................................................

@plac.annotations(
    base_name  = ('use base name "B" for subdirectory names',   'option', 'b'),
    dc_file    = ('read DC terms from file "D"',                'option', 'd'),
    epxml_file = ('read EP3 XML content from file "E"',         'option', 'e'),
    fetch_list = ('read list of records to get from file "F"',  'option', 'f'),
    output_dir = ('write output to directory "O"',              'option', 'o'),
    pswd       = ('eprints user password',                      'option', 'p'),
    user       = ('eprints user name',                          'option', 'u'),
    debug      = ('turn on debugging',                          'flag',   'D'),
    no_bags    = ('do not create bags; just leave the content', 'flag',   'N'),
)

def main(base_name = 'B', dc_file = 'D', epxml_file = 'E', fetch_list = 'F',
         output_dir = 'O', user = 'U', pswd = 'P', debug = False,
         no_bags = False):
    '''eprints2bag bags up CODA Eprints content as BagIt bags.

The eprints records to be written will be limited to the list of eprint
numbers found in the file given by the option -f.  If no -f option is given,
all Eprints records found in the DC file will be used.  The value of -f can
also be one or more integers separated by commas (e.g., -f 54602,54604), or a
range of numbers separated by a dash (e.g., -f 1-100, which is interpreted as
the list of numbers 1, 2, ..., 100 inclusive).  In those cases, the records
written will be limited to those numbered.  (Useful for testing.)

A Dublin Core (DC) file from Eprints must be provided as option -d, and
an EP3 XML file has to be provided using option -e.  This program uses the
DC file as its working basis; i.e., it iterates over the DC file and looks up
associated information in the XML file, and not the other way around.

This program writes the output in the directory given by the command line
option -o.  If the directory does not exist, this program will create it.  If
the directory does exist, it will be overwritten with the new content.  The
result of running this program will be individual directories underneath the
directory -o, with each subdirectory named according to "BASENAME-NUMBER"
where BASENAME is given by the -b option and the NUMBER is the Eprints number
for a given entry).  The BASENAME is "caltechauthors" by default.  Each
directory will contain has DC, EP3XML, and document file(s) found in the
entry.

Documents associated with each record will be fetched over the network.  The
list of documents for each record is determined from XML file, in the
<documents> element.  Downloading some documents requires using a user
login and password.  These can be supplied using the command-line arguments
-u and -p, respectively.

The final step of this program is to create BagIt bags from the contents of
the subdirectories created for each record, then tar up and gzip the bag
directory.  This is done by default, after the documents are downloade for
each record, unless the -N option is given.  Note that creating bags is a
destructive operation: it replaces the individual directories of each record
with a restructured directory corresponding to the BagIt format.
'''
    # Process arguments -------------------------------------------------------

    if dc_file == 'D' or epxml_file == 'E':
        exit('Must provide values for both the -d and -e options.')

    if base_name == 'B':
        base_name = 'caltechauthors'

    if not path.isabs(dc_file):
        dc_file = path.realpath(path.join(os.getcwd(), dc_file))
    if not path.exists(dc_file):
        exit('File not found: {}'.format(dc_file))
    if not readable(dc_file):
        exit('File not readable: {}'.format(dc_file))

    if not path.isabs(epxml_file):
        epxml_file = path.realpath(path.join(os.getcwd(), epxml_file))
    if not path.exists(epxml_file):
        exit('File not found: {}'.format(epxml_file))
    if not readable(epxml_file):
        exit('File not readable: {}'.format(epxml_file))

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
            exit('File not found: {}'.format(fetch_list))
        if not readable(fetch_list):
            exit('File not readable: {}'.format(fetch_list))
        with open(fetch_list, 'r', encoding = 'utf-8-sig') as file:
            wanted = [id.strip() for id in file.readlines()]
    else:
        wanted = []

    if output_dir == 'O':
        exit('Must provide an output directory using the -o option')
    if not path.isabs(output_dir):
        output_dir = path.realpath(path.join(os.getcwd(), output_dir))
    if path.isdir(output_dir):
        if not writable(output_dir):
            exit('Directory not writable: {}'.format(output_dir))

    if user == 'U':
        user = None
    if pswd == 'P':
        pswd = None

    # Do the real work --------------------------------------------------------

    try:
        print('Reading {} ...'.format(dc_file))
        # Reading the entire file into memory is inefficient, but works for
        # now.  When the day comes when there are too many entries for this
        # approach, we can rewrite this then.
        with open(dc_file, 'r', encoding = 'utf-8-sig') as file:
            dc_content = file.read().split('\n\n')

        if len(wanted) >= 31998 or (not wanted and len(dc_content) >= 31998):
            exit("Can't process more than 31,998 entries due to file system limitations.")

        print('Reading {} ...'.format(epxml_file))
        epxml_content = etree.parse(epxml_file).getroot()

        print('Output will be written under directory {}'.format(output_dir))
        if not path.exists(output_dir):
            os.mkdir(output_dir)

        count = 0
        missing = wanted.copy()
        for dc_blob in dc_content:
            record = eprint_dc_dict(dc_blob)
            number = eprint_number(record)
            # Skip if not in our wanted list and we're not writing everything.
            if wanted and number not in wanted:
                continue
            # Create the output subdirectory and write the DC and XML output.
            record_dir = path.join(output_dir, base_name + '-' + str(number))
            print('Creating {}'.format(record_dir))
            make_dir(record_dir)
            xml_element = eprint_xml(number, epxml_content)
            write_record(number, dc_blob, xml_element, base_name, record_dir)
            # Download any documents referenced in the XML record.
            associated_documents = eprint_documents(xml_element)
            download_files(associated_documents, user, pswd, record_dir)
            # Bag up, tar up, and gzip the directory by default.
            if not no_bags:
                print('Making bag out of {}'.format(record_dir))
                bagit.make_bag(record_dir, checksums = ["sha256", "sha512", "md5"])
                tar_file = record_dir + '.tgz'
                print('Creating {}'.format(tar_file))
                make_tarball(record_dir, tar_file)
                print('Deleting {}'.format(record_dir))
                shutil.rmtree(record_dir)
            # Track what we've done so far.
            count += 1
            if wanted and number in wanted:
                missing.remove(number)
    except KeyboardInterrupt as err:
        exit('Quitting.')
    except Exception as err:
        if debug:
            import pdb; pdb.set_trace()
        print('{}\n{}'.format(str(err), traceback.format_exc()))

    print('Done. Wrote {} Eprints records to {}/.'.format(count, output_dir))
    if len(missing) > 0:
        if len(missing) > 500:
            print('*** Note: > 500 records requested with -f were not found')
        else:
            print('*** Note: the following requested records were not found:')
            print('*** ' + ', '.join(missing) + '.')


# If this is windows, we want the command-line args to use slash intead
# of hyphen.

if ON_WINDOWS:
    main.prefix_chars = '/'


# Main entry point.
# ......................................................................
# The following allows users to invoke this using "python3 -m eprints2bag".

if __name__ == '__main__':
    plac.call(main)


# For Emacs users
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:

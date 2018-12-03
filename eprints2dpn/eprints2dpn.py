#!/usr/bin/env python3
# =============================================================================
# @file    eprints2dpn.py
# @brief   Create DPN-ready gzip'ed tarballs of BagIt bags from Eprints content
# @author  Michael Hucka <mhucka@caltech.edu>
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/eprints2dpn
# =============================================================================

import bagit
from   collections import defaultdict
import errno
import lxml.etree as etree
import os
from   os import path
import plac
import requests
import shutil
import tarfile


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
    '''eprints2dpn bags up Eprints content for deposition to DPN.

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


# Helper functions.
# ......................................................................

def readable(dest):
    '''Returns True if the given 'dest' is accessible and readable.'''
    return os.access(dest, os.F_OK | os.R_OK)


def writable(dest):
    '''Returns True if the destination is writable.'''
    return os.access(dest, os.F_OK | os.W_OK)


def make_dir(dir_path):
    try:
        os.mkdir(dir_path)
    except OSError as err:
        if err.errno == errno.EEXIST:
            print('Reusing existing directory {}'.format(dir_path))
        else:
            raise


def make_tarball(source_dir, tarball_path):
    current_dir = os.getcwd()
    try:
        # cd to get a tarball with only the source_dir and not the full path.
        os.chdir(path.dirname(source_dir))
        with tarfile.open(tarball_path, "w:gz") as tar_file:
            for root, dirs, files in os.walk(path.basename(source_dir)):
                for file in files:
                    tar_file.add(path.join(root, file))
    finally:
        os.chdir(current_dir)


def eprint_dc_dict(dc_text):
    '''Take a block of text representing Dublin Core, and return a dict.'''
    # Each item is a string representing DC info, with embedded newlines.  We
    # split on the newlines, then split again on the ':' and enter the pairs
    # from the ':' split into a dictionary.
    record = defaultdict(list)
    for pair in [line.split(':', 1) for line in dc_text.split('\n')]:
        if len(pair) == 2:
            record[pair[0].strip()].append(pair[1].strip())
    return record


def eprint_xml(number, epxml):
    node = epxml.find(xpath_for_record(number))
    if node is None:
        exit('Cannot find {} in XML file'.format(number))
    else:
        return node


def eprint_number(record):
    # There is no explicit eprints identifier in the DC format (why not?), so
    # we have to get it from the URL stored as one of the 'relation' values.
    # This will be a string like 'https://authors.library.caltech.edu/4/'.
    if 'relation' not in record:
        print('Record without a "relation" value: {}'.format(record['title']))
        return ''
    for value in record['relation']:
        if value.startswith('https://authors.library.caltech.edu'):
            # Remove trailing slash and grab the number at the end.
            return value.strip('/').split('/')[-1]


def eprint_documents(xml):
    files = []
    for document in xml.findall('.//{http://eprints.org/ep2/data/2.0}documents'):
        for url in document.findall('.//{http://eprints.org/ep2/data/2.0}url'):
            files.append(url.text)
    return files


def write_record(number, dc, xml, base_name, dir_path):
    # Write out a text file containing the DC content.
    dc_file_name = base_name + '-' + str(number) + '-DC.txt'
    with open(path.join(dir_path, dc_file_name), 'w') as file:
        file.write(dc)

    # Write out another file containing the XML content.
    xml_file_name = base_name + '-' + str(number) + '.xml'
    with open(path.join(dir_path, xml_file_name), 'w') as file:
        file.write("<?xml version='1.0' encoding='utf-8'?>\n")
        file.write("<eprints xmlns='http://eprints.org/ep2/data/2.0'>\n")
        file.write('  ' + etree.tostring(xml, encoding='UTF-8').decode().rstrip() + '\n')
        file.write("</eprints>")


def xpath_for_record(number):
    ns = '{http://eprints.org/ep2/data/2.0}'
    prefix = 'https://authors.library.caltech.edu/id/eprint'
    return './/{}eprint[@id="{}/{}"]'.format(ns, prefix, number)


def download_files(downloads_list, user, pswd, output_dir):
    for item in downloads_list:
        file = path.realpath(path.join(output_dir, path.basename(item)))
        print('Downloading {}'.format(item))
        error = download(item, user, pswd, file)
        if error:
            print('*** Failed to download {}'.format(item))
            print('*** Reason: {}'.format(error))


def download(url, user, password, local_destination):
    '''Download the 'url' to the file 'local_destination'.  If an error
    occurs, returns a string describing the reason for failure; otherwise,
    returns False to indicate no error occurred.
    '''
    try:
        req = requests.get(url, stream = True, auth = (user, password))
    except requests.exceptions.ConnectionError as err:
        if err.args and isinstance(err.args[0], urllib3.exceptions.MaxRetryError):
            return 'Unable to resolve destination host'
        else:
            return str(err)
    except requests.exceptions.InvalidSchema as err:
        return 'Unsupported network protocol'
    except Exception as err:
        return str(err)

    # Interpret the response.
    code = req.status_code
    if code == 202:
        # Code 202 = Accepted, "received but not yet acted upon."
        sleep(1)                        # Sleep a short time and try again.
        return download(url, local_destination)
    elif 200 <= code < 400:
        # The following originally started out as the code here:
        # https://stackoverflow.com/a/16696317/743730
        with open(local_destination, 'wb') as f:
            for chunk in req.iter_content(chunk_size = 1024):
                if chunk:
                    f.write(chunk)
        req.close()
        return False                    # No error.
    elif code in [401, 402, 403, 407, 451, 511]:
        return "Access is forbidden or requires authentication"
    elif code in [404, 410]:
        return "No content found at this location"
    elif code in [405, 406, 409, 411, 412, 414, 417, 428, 431, 505, 510]:
        return "Server returned code {} -- please report this".format(code)
    elif code in [415, 416]:
        return "Server rejected the request"
    elif code == 429:
        return "Server blocking further requests due to rate limits"
    elif code == 503:
        return "Server is unavailable -- try again later"
    elif code in [500, 501, 502, 506, 507, 508]:
        return "Internal server error"
    else:
        return "Unable to resolve URL"


# Main entry point.
# ......................................................................
# The following allows users to invoke this using "python3 -m handprint".

if __name__ == '__main__':
    plac.call(main)


# For Emacs users
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:

'''
eprints.py: EPrints-specific utilities

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   collections import defaultdict
import lxml.etree as etree
import os
from   os import path
import shutil


# Constants.
# .............................................................................

_EPRINTS_XMLNS = 'http://eprints.org/ep2/data/2.0'
'''
XML namespace used in EPrints XML output.
'''


# Main functions.
# .............................................................................

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
    for document in xml.findall('.//{{}}documents'.format(_EPRINTS_XMLNS)):
        for url in document.findall('.//{{}}url'.format(_EPRINTS_XMLNS)):
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
        file.write("<eprints xmlns=''>\n".foramt(_EPRINTS_XMLNS))
        file.write('  ' + etree.tostring(xml, encoding='UTF-8').decode().rstrip() + '\n')
        file.write("</eprints>")


def xpath_for_record(number):
    prefix = 'https://authors.library.caltech.edu/id/eprint'
    return './/{{}}eprint[@id="{}/{}"]'.format(_EPRINTS_XMLNS, prefix, number)

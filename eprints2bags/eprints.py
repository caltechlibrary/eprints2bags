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

import eprints2bag
from   eprints2bag.exceptions import *
from   eprints2bag.network import net


# Constants.
# .............................................................................

_EPRINTS_XMLNS = 'http://eprints.org/ep2/data/2.0'
'''
XML namespace used in EPrints XML output.
'''


# Main functions.
# .............................................................................

def eprints_api(url, op, user, password):
    '''Return a full EPrints API URL, complete with user & password, and ending
    with an operation string given by 'op'.'''
    start = url.find('//')
    if start < 0:
        raise BadURL('Unable to parse "{}" as a normal URL'.format(url))
    return url[:start + 2] + user + ':' + password + '@' + url[start + 2:] + op


def eprints_records_list(base_url, user, password):
    url = eprints_api(base_url, '/eprint', user, password)
    (response, error) = net('get', url)
    if error:
        raise error
    if not response.content:
        raise ServiceFailure('Failed to get a list back from server')
    xml = etree.fromstring(response.content)
    # The content from this call is in XHTML format.  It looks like this, and
    # the following loop extracts the numbers from the <li> elements:
    #
    #   <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    #       "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    #   <html xmlns="http://www.w3.org/1999/xhtml">
    #   <head>
    #     <title>EPrints REST: Eprints DataSet</title>
    #     <style type="text/css">
    #       body { font-family: sans-serif; }
    #     </style>
    #   </head>
    #   <body>
    #     <h1>EPrints REST: Eprints DataSet</h1>
    #   <ul>
    #   <li><a href='4/'>4/</a></li>
    #   <li><a href='4.xml'>4.xml</a></li>
    #   <li><a href='5/'>5/</a></li>
    #   <li><a href='5.xml'>5.xml</a></li>
    #   ...
    #
    numbers = []
    for node in xml.findall('.//{http://www.w3.org/1999/xhtml}a'):
        if 'href' in node.attrib and node.attrib['href'].endswith('xml'):
            numbers.append(node.attrib['href'].split('.')[0])
    return numbers


def eprints_xml(number, base_url, user, password):
    url = eprints_api(base_url, '/eprint/{}.xml'.format(number), user, password)
    (response, error) = net('get', url)
    if error:
        raise error
    return etree.fromstring(response.content)


def eprints_documents(xml):
    files = []
    for document in xml.findall('.//{' + _EPRINTS_XMLNS + '}documents'):
        for url in document.findall('.//{' + _EPRINTS_XMLNS + '}url'):
            # Skip certain internal documents:
            if 'indexcodes.txt' in url.text:
                continue
            files.append(url.text)
    return files


def write_record(number, xml, dir_prefix, dir_path):
    xml_file_name = dir_prefix + str(number) + '.xml'
    with open(path.join(dir_path, xml_file_name), 'w') as file:
        file.write(etree.tostring(xml, encoding='UTF-8').decode().rstrip() + '\n')

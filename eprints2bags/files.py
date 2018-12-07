'''
files.py: utilities for working with files.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import errno
import gzip
import os
from   os import path
from   PIL import Image
import sys
import tarfile

import eprints2bags
from   eprints2bags.debug import log
from   eprints2bags.exceptions import *


# Main functions.
# .............................................................................

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
            if __debug__: log('Reusing existing directory {}', dir_path)
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


def verify_tarball(tarball_path):
    '''Check the integrtive of a tar file and raise an exception if needed.'''
    # Algorithm originally from https://stackoverflow.com/a/32312857/743730
    try:
        with tarfile.open(tarball_path) as tfile:
            for member in tfile.getmembers():
                with tfile.extractfile(member.name) as target:
                    for chunk in iter(lambda: target.read(1024), b''):
                        pass
    except:
        raise CorruptedContent('Failed to verify file "{}"'.format(tarball_path))

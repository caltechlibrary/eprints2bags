'''
files.py: utilities for working with files.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2019 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import gzip
import os
from   os import path
from   psutil import disk_partitions
import shutil
from   sidetrack import log
import sys
import tarfile
import tempfile
import zipfile
from   zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED

import eprints2bags
from   eprints2bags.exceptions import *


# Constants.
# .............................................................................

KNOWN_SUBDIR_LIMITS = {
    'ext2'  : 31998,         # https://en.wikipedia.org/wiki/Ext2
    'ext3'  : 31998,         # https://en.wikipedia.org/wiki/Ext3
    'ext4'  : sys.maxsize,   # https://en.wikipedia.org/wiki/Ext4
    'hfs'   : 2147483648,    # https://support.apple.com/en-us/HT201711
    'apfs'  : 2147483648,    # can't find number; using hfs+ value
    'ntfs'  : 4294967295,    # https://en.wikipedia.org/wiki/NTFS
    'xfs'   : sys.maxsize,   # https://access.redhat.com/articles/rhel-limits
    'zfs'   : sys.maxsize,   # https://access.redhat.com/articles/rhel-limits
    'gfs'   : sys.maxsize,   # https://access.redhat.com/articles/rhel-limits
    'gfs2'  : sys.maxsize,   # https://access.redhat.com/articles/rhel-limits
    'exfat' : 2796202,       # https://en.wikipedia.org/wiki/ExFAT
    'fat32' : 65534,
}
'''Maximum number of subdirectories for different types of file systems.'''


# Main functions.
# .............................................................................

def readable(dest):
    '''Returns True if the given 'dest' is accessible and readable.'''
    return os.access(dest, os.F_OK | os.R_OK)


def writable(dest):
    '''Returns True if the destination is writable.'''

    # Helper function to test if a directory is writable.
    def dir_writable(dir):
        # This is based on the following Stack Overflow answer by user "zak":
        # https://stackoverflow.com/a/25868839/743730
        try:
            testfile = tempfile.TemporaryFile(dir = dir)
            testfile.close()
        except (OSError, IOError) as e:
            return False
        return True

    if path.exists(dest) and not path.isdir(dest):
        # Path is an existing file.
        return os.access(dest, os.F_OK | os.W_OK)
    elif path.isdir(dest):
        # Path itself is an existing directory.  Is it writable?
        return dir_writable(dest)
    else:
        # Path is a file but doesn't exist yet. Can we write to the parent dir?
        return dir_writable(path.dirname(dest))


def fs_type(p):
    '''Return the type of the file system on which the path 'p' is located.'''
    # Code modified from https://stackoverflow.com/a/25286268/743730
    root_type = None
    for part in disk_partitions():
        if part.mountpoint == '/':
            root_type = part.fstype
            continue
        if p.startswith(part.mountpoint):
            root_type = part.fstype
    return root_type


def make_dir(dir_path):
    '''Creates directory 'dir_path' (including intermediate directories).'''
    if path.isdir(dir_path):
        if __debug__: log(f'reusing existing directory {dir_path}')
        return
    else:
        if __debug__: log(f'creating directory {dir_path}')
        # If this gets an exception, let it bubble up to caller.
        os.makedirs(dir_path)


def archive_extension(type):
    if type.endswith('zip'):
        return '.zip'
    elif type.endswith('tar'):
        return '.tar' if type.startswith('uncompressed') else '.tar.gz'
    else:
        raise InternalError(f'Unrecognized archive format: {type}')


def create_archive(archive_file, type, source_dir, comment = None):
    root_dir = path.dirname(path.normpath(source_dir))
    base_dir = path.basename(source_dir)
    if type.endswith('zip'):
        format = ZIP_STORED if type.startswith('uncompress') else ZIP_DEFLATED
        current_dir = os.getcwd()
        try:
            if root_dir != '':
                os.chdir(root_dir)
            with zipfile.ZipFile(archive_file, 'w', format) as zf:
                for root, dirs, files in os.walk(base_dir):
                    for file in files:
                        zf.write(os.path.join(root, file))
                if comment:
                    zf.comment = comment.encode()
        finally:
            os.chdir(current_dir)
    else:
        if type.startswith('uncompress'):
            shutil.make_archive(source_dir, 'tar', root_dir, base_dir)
        else:
            shutil.make_archive(source_dir, 'gztar', root_dir, base_dir)


def verify_archive(archive_file, type):
    '''Check the integrity of an archive and raise an exception if needed.'''
    if type.endswith('zip'):
        error = ZipFile(archive_file).testzip()
        if error:
            raise CorruptedContent(f'Failed to verify file "{archive_file}"')
    else:
        # Algorithm originally from https://stackoverflow.com/a/32312857/743730
        tfile = None
        try:
            tfile = tarfile.open(archive_file)
            for member in tfile.getmembers():
                content = tfile.extractfile(member.name)
                if content:
                    for chunk in iter(lambda: content.read(1024), b''):
                        pass
        except Exception as ex:
            raise CorruptedContent(f'Failed to verify file "{archive_file}"')
        finally:
            if tfile:
                tfile.close()

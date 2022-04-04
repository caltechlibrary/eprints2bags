'''
eprints2bags: package up EPrints materials as BagIt bags

This is a program to encapsulate the process of downloading content from
EPrints and encapsulating it as BagIt-format bags for deposition into
storage/archiving systems.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

This work is based on code originally written in Perl by Besty Coles
(betsycoles@gmail.com).  The original code can be found in the 'historical'
subdirectory in the repo at https://github.com/caltechlibrary/eprints2bags/

Copyright
---------

Copyright (c) 2019-2020 by the California Institute of Technology.  This code
is open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

# Package metadata ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#  ╭────────────────────── Notice ── Notice ── Notice ─────────────────────╮
#  |    The following values are automatically updated at every release    |
#  |    by the Makefile. Manual changes to these values will be lost.      |
#  ╰────────────────────── Notice ── Notice ── Notice ─────────────────────╯

__version__     = '1.10.0'
__description__ = 'Download EPrints content and save it in BagIt-format bags.'
__url__         = 'https://github.com/caltechlibrary/eprints2bags'
__author__      = 'Michael Hucka'
__email__       = 'mhucka@caltech.edu'
__license__     = 'BSD 3-clause'


# Miscellaneous utilities.
# .............................................................................

def print_version():
    print(f'{__name__} version {__version__}')
    print(f'Authors: {__author__}')
    print(f'URL: {__url__}')
    print(f'License: {__license__}')

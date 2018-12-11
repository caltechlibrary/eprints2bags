'''
constants: global constants for eprints2bags.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import sys

ON_WINDOWS = sys.platform.startswith('win')
'''True if we're running on a Windows system, False otherwise.'''

KEYRING = "org.caltechlibrary.eprints2bags"
'''The name of the keyring used to store Caltech access credentials, if any.'''

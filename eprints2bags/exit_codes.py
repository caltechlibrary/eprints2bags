'''
exit_codes.py: define exit codes for program return values

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2020 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from enum import IntEnum

class ExitCode(IntEnum):
    success        = 0
    user_interrupt = 1
    bad_arg        = 2
    no_network     = 3
    file_error     = 4
    server_error   = 5
    exception      = 6

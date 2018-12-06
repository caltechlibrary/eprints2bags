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

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from .__version__ import __version__, __title__, __description__, __url__
from .__version__ import __author__, __email__
from .__version__ import __license__, __copyright__

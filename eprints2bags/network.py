'''
network.py: miscellaneous network utilities for eprints2bags.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import http.client
from   http.client import responses as http_responses
from   os import path
import requests
from   time import sleep
import ssl
import urllib
from   urllib import request

import eprints2bags
from   eprints2bags.debug import log
from   eprints2bags.exceptions import *


# Main functions.
# .............................................................................

def network_available():
    '''Return True if it appears we have a network connection, False if not.'''
    r = None
    try:
        r = urllib.request.urlopen("http://www.google.com")
        return True
    except Exception:
        if __debug__: log('Could not connect to https://www.google.com')
        return False
    if r:
        r.close()


def download_files(downloads_list, user, pswd, output_dir, say):
    for item in downloads_list:
        file = path.realpath(path.join(output_dir, path.basename(item)))
        say.info('Downloading {}', item)
        error = download(item, user, pswd, file)
        if error:
            say.error('*** Failed to download {}', item)
            say.error('*** Reason: {}', error)


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


def net(get_or_post, url, polling = False, **kwargs):
    '''Gets or posts the 'url' with optional keyword arguments provided.
    Returns a tuple of (response, exception), where the first element is
    the response from the get or post http call, and the second element is
    an exception object if an exception occurred.  If no exception occurred,
    the second element will be None.  This allows the caller to inspect the
    response even in cases where exceptions are raised.

    If keyword 'polling' is True, certain statuses like 404 are ignored and
    the response is returned; otherwise, they are considered errors.
    '''
    try:
        if __debug__: log('HTTP {} {}', get_or_post, url)
        http_method = requests.get if get_or_post == 'get' else requests.post
        req = http_method(url, **kwargs)
    except requests.exceptions.ConnectionError as ex:
        if ex.args and isinstance(ex.args[0], urllib3.exceptions.MaxRetryError):
            return (req, NetworkFailure('Unable to resolve destination host'))
        else:
            return (req, NetworkFailure(str(ex)))
    except requests.exceptions.InvalidSchema as ex:
        return (req, NetworkFailure('Unsupported network protocol'))
    except Exception as ex:
        return (req, ex)

    # Interpret the response.
    code = req.status_code
    error = None
    if code in [404, 410] and not polling:
        error = NoContent("No content found at this location")
    elif code in [401, 402, 403, 407, 451, 511]:
        error = AuthenticationFailure("Access is forbidden or requires authentication")
    elif code in [405, 406, 409, 411, 412, 414, 417, 428, 431, 505, 510]:
        error = ServiceFailure("Server sent {} -- please report this".format(code))
    elif code in [415, 416]:
        error = ServiceFailure("Server rejected the request")
    elif code == 429:
        error = RateLimitExceeded("Server blocking further requests due to rate limits") 
    elif code == 503:
        error = ServiceFailure("Server is unavailable -- try again later")
    elif code in [500, 501, 502, 506, 507, 508]:
        error = ServiceFailure("Internal server error")
    elif not (200 <= code < 400):
        error = NetworkFailure("Unable to resolve URL")
    return (req, error)

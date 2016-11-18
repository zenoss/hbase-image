#!/usr/bin/env python

##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import time
import logging
from functools import wraps

def backoff(maxtries = 5, delay = 1, backoff = 2):
    def wrap(f):

        @wraps(f)        
        def retry_f(*args, **kwargs):
            mdelay = delay
            for t in xrange(maxtries):
                result = f(*args, **kwargs)
                if result:
                    return result
                else:
                    logging.info("attempt failed.")
                    if t < (maxtries - 1):
                        logging.info("retrying in %d", mdelay)
                        time.sleep(mdelay)
                    mdelay *= backoff
            logging.info("Giving up.")
            return None

        return retry_f
    
    return wrap


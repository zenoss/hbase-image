#!/usr/bin/env python
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
from __future__ import print_function
import random
import sys
import time


def simulate_error(m):
    print('ERROR on stderr blah blah blah', file=sys.stderr)


def simulate_bad_data(m):
    print("ERROR blah blah blah")



def simulate_good_data(m):
    for i in range(100):
        print("{} {} {} {} {} {}".format(m, 1477591782 + 300 * i,
                                         random.random(), "foo=bar",
                                         "contextUUID=012345{}".format(i % 7),
                                         "key=/argle/bargle/foo/" + m),
              file=sys.stdout)



def simulate_scan(argv):
    matches = (x for x in sys.argv if 'metric' in x)
    for m in matches:
        time.sleep(random.random() * 1)
        if 'err' in m:
            simulate_error(m)
            exit(1)
        elif 'bad' in m:
            simulate_bad_data(m)
            exit(1)
        else:
            simulate_good_data(m)


def simulate_import(argv):
    if any('boom' in x for x in argv):
        #simulate exception
        print("ERROR going boom!", file=sys.stderr)
        raise Exception('boom')
    print("simulate_import({})".format(argv))



def main():
    print("faketsdb call {}".format(sys.argv))
    if "scan" in sys.argv:
        simulate_scan(sys.argv)
    elif "import" in sys.argv:
        simulate_import(sys.argv)
    else:
        print()



if __name__ == '__main__':
    main()
#!/usr/bin/env python
from __future__ import print_function
import random
import sys
import time

__author__ = 'morr'


def simulate_error(m):
    print('Exception on stderr blah blah blah', file=sys.stderr)

def simulate_bad_data(m):
    print("Exception blah blah blah")


def simulate_good_data(m):
    for i in range(100):
        print("{} {} {} {} {} {}".format(m, 1477591782 + 300 * i,
                                         random.random(), "foo=bar",
                                         "contextUUID=012345{}".format(i % 7),
                                         "key=/argle/bargle/foo/" + m),
              file=sys.stdout)
    pass

def main():
    matches = (x for x in sys.argv if 'metric' in x)
    for m in matches:
        time.sleep(random.random() * 3)
        if '3' in m:
            simulate_error(m)
        elif '7' in m:
            simulate_bad_data(m)
        else:
            simulate_good_data(m)


if __name__ == '__main__':
    main()
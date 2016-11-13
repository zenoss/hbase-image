#!/usr/bin/env python
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import argparse
import random
import time


def args():
    parser = argparse.ArgumentParser(description="Generate fake data for "
                                                 "opentsdb import")
    parser.add_argument("-i", "--interval", type=int, default=300,
                        help="time interval between data points")
    parser.add_argument("-n", "--num-points", type=int, default=1000,
                        dest="num_points", help="number of points to generate")
    parser.add_argument("-m", "--metric-name", default="fakemetric",
                        dest="metric_name", help="name of fake metric")
    return parser.parse_args()


class FakeData(object):
    def __init__(self, opts):
        self.i = opts.interval
        self.n = opts.num_points
        self.metric = opts.metric_name

    def main(self):
        now = int(time.time())
        start = now - (self.n * self.i)
        for t in range(start, now, self.i):
            print ("{:s} {:d} {:f} host=fake".format(self.metric, t, random.uniform(0.1, 1000.0)))

if __name__ == '__main__':
    FakeData(args()).main()
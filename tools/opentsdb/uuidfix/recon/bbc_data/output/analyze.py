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
import matplotlib.pyplot as plt
import numpy as np

def args():
    """
    standard argparse definition for command-line arguments
    :return: object with parsed argument values
    """
    parser = argparse.ArgumentParser(description="analyze distribution of "
                                                 "metric data")
    parser.add_argument("-f", "--filename",
                        help="File containing list of metrics to process")
    return parser.parse_args()


def showplot(points, bins, label):
    print "max:{}".format(max(points))
    print "len: {}".format(len(points))
    plt.hist(points, bins, normed=True)
    plt.title("{}".format(label))
    plt.show()


def run(filename):
    print opts
    dist = []
    bigs = []
    littles = []
    with open(filename) as f:
        for line in f:
            fields = line.split(' ')
            if len(fields) == 6:
                lc = int(fields[3])
                dist.append(lc)
                if lc < 150:
                    littles.append(lc)
                else:
                    bigs.append(lc)
            else:
                print "ignoring line. fields = {}".format(repr(fields))
    # showplot(dist, 'fd',"dist")
    # showplot(bigs, 'auto',"bigs")
    # showplot(littles, 'auto', "littles")
    bins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30,
            40, 50, 70, 100, 150, 200, 250, 300, 400, 500, 1000, 1500, 2000,
            2500, 5000, 10000, 20000, 50000, 100000, 500000, 1000000, 5000000]
    hist, bin_edges = np.histogram(dist, bins)
    for i in range(len(hist)):
        print "{:10} {:10} {:10}".format(bin_edges[i], hist[i], bin_edges[i+1])
    # print h

if __name__ == '__main__':
    opts = args()
    print opts
    run(opts.filename)

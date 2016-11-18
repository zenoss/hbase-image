#!/usr/bin/env python
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import itertools

def getgen(n=100):
    return (x * x for x in range(n))

def next_batch(g, n):
    return itertools.islice(g,n)


def do_stuff(g):
    n = 0
    items = []
    for x in g:
        n += 1
        items.append(x)
    print "do_stuff: {}".format(items)
    return n

g = getgen()
t = 0
b = 0
while True:
    n = do_stuff(next_batch(g, 27))
    b += 1
    t += n
    if n == 0:
        break

print "All done. {} items processed in {} batches.".format(t, b)


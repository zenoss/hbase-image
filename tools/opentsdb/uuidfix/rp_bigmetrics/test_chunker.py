#!/usr/bin/env python
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
from chunker import batch, gen_batch

import unittest

class MyTestCase(unittest.TestCase):
    def test_batch(self):
        for b in batch((x*x for x in range(1000)),37):
            self.assertEqual(len(b), 37)

class test_gen_batch(unittest.TestCase):
    def test_something(self):
        batch_count = 0
        for b in gen_batch((x*x for x in range(1000)),37):
            self.assertEqual(sum(1 for _ in b), 37)
            batch_count += 1
        self.assertEqual(batch_count, 1000 / 37)



if __name__ == '__main__':
    unittest.main()

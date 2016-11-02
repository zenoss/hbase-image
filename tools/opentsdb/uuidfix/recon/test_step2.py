##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import unittest
from step2 import MetricKeyTabulator


class MetricKeyTabulatorTest(unittest.TestCase):
    def test_mkt(self):
        mkt = MetricKeyTabulator()
        mkt.add("metric1", "key1", "None", 5)
        mkt.add("metric1", "key2", "None", 3)
        self.assertFalse(mkt.has_multiguid_mks())
        self.assertTrue(mkt.has_no_guids())
        mkt.add("metric1", "key1", "guid1", 3)
        self.assertFalse(mkt.has_no_guids())
        self.assertFalse(mkt.has_multiguid_mks())
        mkt.add("metric1", "key3", "", 1)
        self.assertFalse(mkt.has_no_guids())
        self.assertFalse(mkt.has_multiguid_mks())
        mkt.add("metric1", "key3", "aguid", 3)
        self.assertTrue(mkt.has_multiguid_mks())


if __name__ == '__main__':
    unittest.main()

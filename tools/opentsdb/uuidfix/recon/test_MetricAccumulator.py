##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
from metricAccumulator import MetricAccumulator
import datapoint

import unittest

def make_point(metric="metric", tag=None, contextUUID=None):
    kvp = "{} {}".format("tag={}".format(tag) if tag else "", "contextUUID={}" if contextUUID else "")
    return datapoint.Datapoint("{} 12345 1.2345 {}".format(metric, kvp))

class MyTestCase(unittest.TestCase):

    def test_add_point(self):
        subj = MetricAccumulator()
        self.assertEqual(subj.get_stat_count(), 0)
        dp = make_point("metric", "tag", "uuid")
        subj.add_point(dp)
        self.assertEqual(subj.get_stat_count(), 1)

    def test_get_uuid_count(self):
        subj = MetricAccumulator()
        for (metric, tag, uuid) in (
                ("metric", "tag", "uuid"),
                ("metric", "tag", "uuid2"),
                ("metric", "tag", "uuid"),
                ("metric", "tag", "uuid")
        ):
            subj.add_point(make_point(metric, tag, uuid))
        self.assertEqual(subj.get_stat_count(), 4)
        pass

if __name__ == '__main__':
    unittest.main()

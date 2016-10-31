##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
from collections import defaultdict

class MetricAccumulator(object):
    def __init__(self):
        self.stats = defaultdict(int)
        self.stat_count = 0

    def add_point(self, point):
        k = (point.MetricName(), point.Tag("key"), point.Tag("contextUUID"))
        self.stats[k] += 1
        self.stat_count += 1

    def get_stats(self):
        return self.stats

    def get_stat_count(self):
        return self.stat_count

    def get_uuid_count(self):
        pass

    def get_UUIDs_per_key(self):
        """
        Get a dict of (metric,key):contextUUID pairs
        :return:
        """
        pass

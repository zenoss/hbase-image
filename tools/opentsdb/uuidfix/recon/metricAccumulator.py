from collections import defaultdict

__author__ = 'morr'

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

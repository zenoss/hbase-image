##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import time


class Timer(object):
    def __init__(self, total, item="Metric"):
        self.total = total
        self.start_time = time.time()
        self.done = 0
        self.item = item

    def items_completed(self, count=1):
        self.done += count

    # def GetStatCount(self):
    #     return self.done

    def time_left(self):
        return (self.total - self.done) * self.time_per_item()

    def elapsed_time(self):
        return time.time() - self.start_time

    def time_per_item(self):
        if self.done == 0:
            return 0.0
        return float(self.elapsed_time()) / float(self.done)

    def start(self):
        self.start_time = time.time()

    def perf_string(self):
        return "{} {}s processed in {} sec. {}/{}. " \
               "Est time remaining: {}".format(self.done, self.item,
                                               self.elapsed_time(),
                                               self.time_per_item(), self.item,
                                               self.time_left())

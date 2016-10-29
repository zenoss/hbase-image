__author__ = 'morr'

import time

class Timer(object):
    def __init__(self, total, item="Metric"):
        self.total = total
        self.start = time.time()
        self.done = 0
        self.item = item

    def ItemsCompleted(self, count=1):
        self.done += count

    def GetStatCount(self):
        return self.done

    def ElapsedTime(self):
        return time.time() - self.start

    def TimePerItem(self):
        if self.done == 0:
            return 0.0
        return float(self.ElapsedTime())/float(self.done)

    def GetPerfString(self):
        return "{} {}s processed in {} sec. {}/{}".format(self.done, self.item, self.ElapsedTime(), self.TimePerItem(), self.item)
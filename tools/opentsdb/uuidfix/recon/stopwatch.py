import time

__author__ = 'morr'


class stopwatch(object):
    def __init__(self, n):
        self.n = 0
        self.i = 0
        self.start = time.time()
        self.last = self.start

    def update(self, i):
        self.now = time.time()
        self.elapsed = self.now - self.start
        self.rate = (self.now - self.last) / i
        self.last = self.now
        self.etr = (self.n - self.i) * self.elapsed / i


    def percentcomplete(self):
        return self.i / self.n

    def numcomplete(self):
        return self.numcomplete()

    def elapsed(self):
        return self.elapsed

    def remaining(self):
        return self.etr

    def rate(self):
        return self.rate

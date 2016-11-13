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
import logging
import os

import pipegen


def args():
    parser = argparse.ArgumentParser(description="Find and eliminate duplicate "
                                                 "lines in an opentsdb data "
                                                 "file.")
    parser.add_argument("-m", "--metricfile", required=True,
                        help="file containing names of metrics to migrate")
    parser.add_argument("-o", "--outputdir", default="./fd_out",
                        help="directory for output files")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="enable verbose logging")
    return parser.parse_args()


def dedupe(lines, logger=logging.getLogger("finddupes")):
    dupes = []
    latest = {}
    for line in lines:
        mdp = MetricDatapoint.parse(line)
        if latest.get(mdp.keyhash(), MetricDatapoint()).timestamp == \
                mdp.timestamp:
            logger.debug("dupe in {} with tags {} at time {}. "
                         "value={}".format(mdp.metric, str(mdp.tags),
                                           mdp.timestamp, mdp.data))
            dupes.append(mdp)
            # pending = line
        else:
            yield line
        latest[mdp.keyhash()] = mdp


def parsetsdbline(lines):
    for line in lines:
        metric, timestamp, data, rest = line.split(" ", 3)
        yield timestamp, (metric, rest)


class MetricDatapoint(object):
    def __init__(self, *_, **kwargs):
        self.metric = kwargs.get("metric", None)
        self.data = kwargs.get("data", None)
        self.timestamp = kwargs.get("timestamp", None)
        self.tags = kwargs.get("tags", {})

    @property
    def logger(self):
        return logging.getLogger('finddupes.MetricDatapoint')

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        r = "{} at {}:({})".format(self.__class__, id(self), self.__dict__)
        return r

    def keyhash(self):
        return hash((self.metric, str(self.tags)))

    @classmethod
    def parse(cls, s):
        metric, timestamp, data, rest = s.split(" ", 3)
        tags = {}
        for kv in rest.split():
            k, v = kv.split("=")
            tags[k] = v
        return cls(metric=metric, timestamp=timestamp, data=data, tags=tags)


class FindDupes(object):
    def __init__(self):
        pass

    @property
    def logger(self):
        return logging.getLogger('ddrp.FindDupes')

    def dedupe(self, lines):
        dupes = []
        latest = {}
        for line in lines:
            mdp = MetricDatapoint.parse(line)
            if latest.get(mdp.keyhash(), MetricDatapoint()).timestamp == \
                    mdp.timestamp:
                self.logger.info("dupe in {} with tags {} at time {}. "
                                 "value={}".format(mdp.metric, str(mdp.tags),
                                                   mdp.timestamp, mdp.data))
                dupes.append(mdp)
                # pending = line
            else:
                yield line
            latest[mdp.keyhash()] = mdp

    def run(self):
        files = ['fixdata/sample-export.out.gz']
        lc = 0
        for f_in in pipegen.gen_opener(files):
            dupes = []
            fdd = self.dedupe(f_in)
            for _ in fdd:
                lc += 1

            self.logger.info("file {} has {} lines".format(f_in.name, lc))
            for dupe in dupes:
                print dupe


def getlogfile(lf_opts):
    log_dir = os.path.join(lf_opts.outputdir, 'log')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return os.path.join(log_dir, "finddupes.log")


def setup_logging(log_fn, verbose=False):
    logger = logging.getLogger('finddupes')
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logger.setLevel(level)
    fh = logging.FileHandler(log_fn)
    fh.setLevel(level)
    sh = logging.StreamHandler()
    sh.setLevel(level)

    if verbose:
        file_formatter = logging.Formatter('%(filename)s %(lineno)d - '
                                           '%(asctime)s - %(name)s - '
                                           '%(levelname)s - %(message)s')
        stream_formatter = logging.Formatter('%(filename)s %(lineno)d - '
                                             '%(levelname)s - %(message)s')
    else:
        file_formatter = logging.Formatter('%(levelname)s - %(name)s - '
                                           '%(asctime)s - %(message)s')
        stream_formatter = logging.Formatter('%(levelname)s - %(message)s')
    fh.setFormatter(file_formatter)
    sh.setFormatter(stream_formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)


if __name__ == '__main__':
    opts = args()
    logfile = getlogfile(opts)
    print 'logfile = {}'.format(logfile)
    setup_logging(logfile, opts.verbose)
    FindDupes().run()

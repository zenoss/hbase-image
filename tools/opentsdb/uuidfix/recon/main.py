##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

"""
main program to initiate collection of metric data for remediation
of opentsdb issue at customer.
The program will take the list of metrics provided, and divide it up into
batches.
These batches will be farmed out to opentsdb containers, with appropriate
directories bind-mounted in for execution.
"""

import argparse
import logging
import signal
import time
import util


def args():
    """
    standard argparse definition for command-line arguments
    :return: object with parsed argument values
    """
    parser = argparse.ArgumentParser(description="gather data to aid in " +
                                     "fixing opentsdb corruption" +
                                     " due to leaked UIDs")
    parser.add_argument("-v", "--verbose", help="Make output verbose",
                        action="store_true")
    parser.add_argument("-c", "--config", help="opentsdb config file")
    parser.add_argument("-s", "--scriptdir", default=".",
                        help="path to directory where scripts reside")
    parser.add_argument("-w", "--workers", default=2,
                        help="number of worker containers")
    parser.add_argument("-b", "--batchsize", default=100,
                        help="number of metrics to process in a batch")
    parser.add_argument("-d", "--datadir", default="./data",
                        help="path to data directory")
    parser.add_argument("-m", "--metricfile", default="metric_names",
                        help="file containing metrics")
    parser.add_argument("-t", "--tsdb", help="name of opentsdb service",
                        choices=["opentsdb", "reader", "writer"],
                        default="reader")
    return parser.parse_args()


class ReconMain(object):
    """
    class to contain main program functionality
    """
    def __init__(self, options):
        """
        class initializer
        :param options:  argparse options
        :return: none
        """
        self.opts = options
        self.setup_logging()
        self.starttime = time.strftime('%Y%m%d-%H%M%S')


    def setup_logging(self):
        """
        Sets up logging for the class
        """
        log_filename = util.makefilename(self.opts.scriptdir, "main",
                                         self.starttime, ".log")

        if self.opts.verbose:
            logging.basicConfig(filename=log_filename, level=logging.DEBUG)
        else:
            logging.basicConfig(filename=log_filename, level=logging.INFO)


    def run(self):
        """
        this is the 'main loop' for the program.
        :return:
        """
        self.setup_logging()
        "serviced", "service", "shell", servicename

        print "here we are!"


if __name__ == "__main__":
    signal.signal(signal.SIGUSR1, util.handle_pdb)
    main = ReconMain(args())
    main.run()

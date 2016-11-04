#!/usr/bin/env python

##############################################################################
#
# Copyright (C) Zenoss, Inc. 2016, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import unittest
import tsdbworker


class TSDBWorkerTestCase(unittest.TestCase):
    def test_process_run_return(self):
        subject = tsdbworker.TSDBWorker()
        result = subject.run_command(["bash","-c", "exit 1"], "dummy")
        self.assertEqual(result, False, "nonzero exit status should return false")
        result = subject.run_command(["bash","-c", "exit 0"], "dummy")
        self.assertEqual(result, True, "zero exit status should return true")


if __name__ == '__main__':
    unittest.main()

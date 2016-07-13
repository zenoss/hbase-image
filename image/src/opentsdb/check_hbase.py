#!/usr/bin/env python

"""
check_hbase: module to query hbase, looking for tables created by opentsdb.
"""

import argparse
import json
import os
import socket
import urllib2
import logging


LOGGER = logging.getLogger('check_hbase')
LOGGING_SETUP = False


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Check the health of hbase.')
    parser.add_argument('--url', '-u', default='http://127.0.0.1:61000/',
                        help='URL for HBase REST interface')
    LOGGER.debug('parsing args')
    args = parser.parse_args()
    LOGGER.debug('args.url = %s', args.url)
    return args


def get_opentsdb_table_names():
    """Get list of table names to look for."""
    table_names = ('tsdb', 'tsdb-uid', 'tsdb-tree', 'tsdb-meta')
    tenant_id = os.getenv('CONTROLPLANE_TENANT_ID', '')
    if len(tenant_id) > 0:
        tenant_id = tenant_id + '-'
    LOGGER.debug('CONTROLPLANE_TENANT_ID = %s', tenant_id)
    return (tenant_id + s for s in table_names)


def setup_logging():
    """Set up logging for the module."""
    global LOGGING_SETUP
    if not LOGGING_SETUP:
        LOGGER.setLevel(logging.INFO)
        c_hand = logging.StreamHandler()
        c_hand.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - '
                                      '%(name)s.%(funcName)s: %(message)s')
        c_hand.setFormatter(formatter)
        LOGGER.addHandler(c_hand)
        LOGGING_SETUP = True


class CheckHbase(object):
    """
    Class to check various statuses on HBase for OpenTSDB.

    Pass base URL of HBase REST interface to constructor. If not passed,
    will use default of 'http://localhost:61000/'.
    """

    def __init__(self, hbase_rest_url='http://localhost:61000/'):
        self.hbase_rest_url = hbase_rest_url
        setup_logging()
        self.logger = LOGGER

    def query_tables(self):
        """Make REST request to hbase to get tables."""
        url = self.hbase_rest_url
        self.logger.debug('about to query %s', url)
        req = urllib2.Request(url, headers={"Accept": "application/json"})
        table_names = []
        try:
            resp = urllib2.urlopen(req, timeout=3)
            result = json.loads(resp.read())
            table_names = [x['name'] for x in result['table']]
            self.logger.debug('query result: %s', result)
            self.logger.debug('table names: %s', table_names)
            resp.close()
        except urllib2.URLError, err:
            self.logger.warn('error opening connection to %s. Reason: %s',
                             url, err.reason)
        except socket.timeout, _:
            self.logger.warn('Timeout connecting to HBase at %s.', url)
        except socket.error, err:
            self.logger.warn('Socket error connecting to HBase at %s. ', url)
        return table_names

    def get_live_nodes(self):
        """
        Returns number of live nodes per HBase REST acll (status/cluster).
        If an error occurs, return is 0.
        """

        live_nodes = 0
        url = self.hbase_rest_url+'status/cluster'
        req = urllib2.Request(url, headers={"Accept": "application/json"})
        try:
            resp = urllib2.urlopen(req, timeout=3)
            result = json.loads(resp.read())
            live_nodes = len(result['LiveNodes'])
        except urllib2.URLError, err:
            self.logger.warn('Error opening connection to %s. Reason: %s',
                             url, err.reason)
        except socket.timeout, err:
            self.logger.warn('Timeout connecting to HBase at %s: %s',
                             url, err)
        except socket.error, err:
            self.logger.warn('Socket error connecting to HBase at %s: %s',
                             url, err)
        return live_nodes

    def check_status(self):
        """Check status of HBase."""
        table_names = self.query_tables()
        for table in get_opentsdb_table_names():
            self.logger.debug('checking table %s', table)
            if table not in table_names:
                self.logger.debug('Table %s was not found in %s. '
                                  'Returning False',
                                  table, table_names)
                return False
        self.logger.debug('All tables found. returning True.')
        return True


def main():
    """Main function."""
    setup_logging()
    args = parse_arguments()
    chb = CheckHbase(hbase_rest_url=args.url)
    status = chb.check_status()
    LOGGER.info("Status is %s", status)

if __name__ == '__main__':
    main()

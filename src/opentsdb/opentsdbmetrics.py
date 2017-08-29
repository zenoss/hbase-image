#!/usr/bin/env python
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2017, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import argparse
import json
import logging
import os
import requests
import sys
import time
import traceback

from pprint import pprint
from collections import defaultdict


log = logging.getLogger('zenoss.servicemetrics')
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log.setLevel(logging.INFO)


class ServiceMetrics(object):
    """
    Simple process that creates a metric gatherer, loops calling for
    internal metrics, then posts those metrics to a consumer.
    """
    DEFAULT_CONSUMER = "http://localhost:22350/api/metrics/store"

    def __init__(self, options):
        self.interval = options.interval
        self.metric_destination = os.environ.get("CONTROLPLANE_CONSUMER_URL", "")
        if self.metric_destination == "":
            self.metric_destination = self.DEFAULT_CONSUMER
        self.session = None
        self.host = options.host

    def run(self):
        gatherer = self.build_gatherer()
        while True:
            time.sleep(self.interval)
            try:
                metrics = gatherer.get_metrics()
                self.push(metrics)
            except Exception:
                log.warning("Failed to gather metrics: " + traceback.format_exc())


    def build_gatherer(self):
        """
        Loads up an object that can gather metrics.
        :return: an instance of an object that implements get_metrics()
        """
        return OpenTSDBMetricGatherer(host=self.host)

    def push(self, metrics):
        if not self.session:
            self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.session.headers.update({'User-Agent': 'Zenoss Service Metrics'})
        post_data = {'metrics': metrics}
        response = self.session.post(self.metric_destination, data=json.dumps(post_data))
        if response.status_code != 200:
            log.warning("Problem submitting metrics: %d, %s", response.status_code, response.text)
            self.session = None
        else:
            log.debug("%d Metrics posted", len(metrics))



class OpenTSDBMetricGatherer(object):
    METRIC_PREFIX = 'zenoss.opentsdb'

    def __init__(self, host=None):
        self.host = host or 'http://localhost:4242'

    def build_metric(self, name, value, timestamp, tags=None):
        try:
            _value = float(value)
        except ValueError as ve:
            _value = None
        if not tags:
            tags = {}
        return {"metric": name,
                "value": _value,
                "timestamp": timestamp,
                "tags": tags}

    def get_metrics(self):
        s = requests.Session()
        opentsdb_stats_url = '%s/api/stats' % self.host
        result = s.get(opentsdb_stats_url, verify=False)
        if result.status_code == 200:
            api_stats = result.json()
            return self._extract_data(api_stats)
        else:
            log.warning("OpenTSDB stats request failed: %d, %s", result.status_code, result.text)

    def _extract_data(self, api_stats):
        metrics = []

        DEFAULT_TAGS = {}

        sought_metrics = (
            'tsd.rpc.exceptions',
            'tsd.http.query.exceptions',
            'tsd.jvm.ramfree',
            'tsd.compaction.count',
            'tsd.datapoints.added',
            'tsd.hbase.flushes',
        )

        for api_stat in api_stats:
            if api_stat.get('metric', '') not in sought_metrics:
                continue
            metric_name = api_stat.get('metric', '')
            metric_name = '%s.%s' % (self.METRIC_PREFIX, metric_name)
            metric_value = api_stat.get('value')
            timestamp = api_stat.get('timestamp', 0)
            tags = {}
            tags.update(DEFAULT_TAGS)
            for k, v in api_stat.get('tags', {}).items():
                tags['zenoss_%s' % k] = v

            metrics.append(self.build_metric(metric_name, metric_value, timestamp, tags))

        metrics_to_tags = {
            'tsd.hbase.rpcs': 'type',
            'tsd.uid.ids-available': 'kind',
        }

        for api_stat in api_stats:
            if api_stat.get('metric', '') not in metrics_to_tags:
                continue
            metric_name = api_stat.get('metric', '')
            metric_suffix = api_stat.get('tags').get(metrics_to_tags[metric_name])
            formatted_metric = '%s.%s.%s' % (self.METRIC_PREFIX, metric_name, metric_suffix)
            metric_value = api_stat.get('value')
            timestamp = api_stat.get('timestamp', 0)
            tags = {}
            tags.update(DEFAULT_TAGS)
            for k, v in api_stat.get('tags', {}).items():
                tags['zenoss_%s' % k] = v

            metrics.append(self.build_metric(formatted_metric, metric_value, timestamp, tags))


        return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interval", dest="interval", type=float,
                        default=30, help="polling interval in seconds")
    parser.add_argument("--host", dest="host", type=str,
                        default='http://localhost:4242', help="OpenTSDB host to query")
    parser.add_argument("-d", "--debug", dest="debug", action='store_true',
                        help="Run metrics collection once and dump to stdout.")
                        
    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)
        stdout = logging.StreamHandler(sys.stdout)
        log.addHandler(stdout)

        sm = ServiceMetrics(options=args)
        gatherer = sm.build_gatherer()
        metrics = gatherer.get_metrics()
        pprint(metrics)

    else:
        sm = ServiceMetrics(options=args)
        sm.run()

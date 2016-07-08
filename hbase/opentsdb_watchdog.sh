#!/bin/bash

wget --timeout=3 --tries=1 -q -O /tmp/tsdbwatchdog.stats http://localhost:4242/api/stats

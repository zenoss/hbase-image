#!/usr/bin/env bash

METRICLIST=./multiguid_metrics
OUTDIR=./metricdata
OLDCONF=./opentsdb_old.conf
NEWCONF=./opentsdb.conf
TSDB=/opt/opentsdb/build/tsdb

mkdir ${OUTDIR}
mkdir ${OUTDIR}/old
mkdir ${OUTDIR}/new

for METRICNAME in $(cat ${METRICLIST})
do
    ${TSDB} scan --config=${OLDCONF} --import 0 sum ${METRICNAME} | gzip > ${OUTDIR}/old/${METRICNAME}.gz
    ${TSDB} scan --config=${NEWCONF} --import 0 sum ${METRICNAME} | gzip > ${OUTDIR}/old/${METRICNAME}.gz
done

tar cvfz ${OUTDIR}.tgz ${OUTDIR}

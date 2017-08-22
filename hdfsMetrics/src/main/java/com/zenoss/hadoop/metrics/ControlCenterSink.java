package com.zenoss.hadoop.metrics;

import org.apache.commons.configuration.SubsetConfiguration;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.hadoop.metrics2.AbstractMetric;
import org.apache.hadoop.metrics2.MetricsRecord;
import org.apache.hadoop.metrics2.MetricsSink;
import org.zenoss.app.consumer.metric.data.Metric;
import org.zenoss.metrics.reporter.HttpPoster;
import org.zenoss.metrics.reporter.MetricBatch;

import java.io.IOException;
import java.net.MalformedURLException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ControlCenterSink implements MetricsSink {
    public final static Log log = LogFactory.getLog(ControlCenterSink.class);
    private Map<String, String> tags = new HashMap<String, String>();
    private List<String> metricPatterns;
    private Map<String, Boolean> metricFilter = new HashMap<String, Boolean>();
    private String metricPrefix = "";

    private HttpPoster metricPoster;

    public void putMetrics(MetricsRecord metricsRecord) {
        MetricBatch metricBatch = new MetricBatch(System.currentTimeMillis() / 1000);
		String metricName = "";
        for (AbstractMetric hadoopMetric : metricsRecord.metrics()) {
            if (includeMetric(hadoopMetric.name())) {
                Metric shortMetric = new Metric(hadoopMetric.name(), metricsRecord.timestamp(), hadoopMetric.value().doubleValue(), tags);
                metricBatch.addMetric(shortMetric);

				if (this.metricPrefix.length() > 0) {
					metricName = this.metricPrefix + hadoopMetric.name();
					Metric metric = new Metric(metricName, metricsRecord.timestamp(), hadoopMetric.value().doubleValue(), tags);
					metricBatch.addMetric(metric);
				}
            }
        }
        try {
            if(metricBatch.getMetrics().size()>0) {
                log.debug("posting metric " + metricBatch.getMetrics().size());
                metricPoster.post(metricBatch);
            }
        } catch (IOException e) {
            log.warn("Error posting metrics with name", e);
        }
    }

    private boolean includeMetric(String metricName) {
        if (metricPatterns == null) {
            return true;
        }
        Boolean filterValue = this.metricFilter.get(metricName);
        if (filterValue != null) {
            log.debug("returning cached value " + filterValue + " for metric " + metricName);
            return filterValue;
        }
        for (String pattern : this.metricPatterns) {
            if (metricName.matches(pattern)) {
                log.debug("metric " + metricName + " matches pattern " + pattern);
                this.metricFilter.put(metricName, true);
                return true;
            }
        }
        log.debug("rejecting metric " + metricName);
        this.metricFilter.put(metricName, false);
        return false;
    }

    public void flush() {

    }

    public void init(SubsetConfiguration subsetConfiguration) {
        log.info("Initializing control center metrics sink");
        tags.put("hdfs", "node");
        String url;
        if (subsetConfiguration.containsKey("host")) {
            log.info("posting metrics to host from configuration file");
            url = subsetConfiguration.getString("host") + HttpPoster.METRIC_API;
        } else {
            url = "http://localhost:22350" + HttpPoster.METRIC_API;
        }
        try {
            HttpPoster.Builder metricPosterBuilder = new HttpPoster.Builder(new java.net.URL(url));
            if (subsetConfiguration.containsKey("username")) {
                metricPosterBuilder.setUsername(subsetConfiguration.getString("username"));
                metricPosterBuilder.setPassword(subsetConfiguration.getString("password"));
            }
            this.metricPoster = metricPosterBuilder.build();
            metricPoster.start();
        } catch (MalformedURLException e) {
            log.error("Unable to build control center sink", e);
        }

        if (subsetConfiguration.containsKey("includedMetrics")) {
            this.metricPatterns = subsetConfiguration.getList("includedMetrics");

        }
        if (subsetConfiguration.containsKey("metricsPrefix")) {
            this.metricPrefix = subsetConfiguration.getString("metricsPrefix");
		}
    }
}

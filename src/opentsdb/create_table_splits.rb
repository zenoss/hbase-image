#!/opt/hbase/bin/hbase org.jruby.Main
# usage: ./create_table.rb tsdb 255
include Java
import org.apache.hadoop.hbase.HBaseConfiguration
import org.apache.hadoop.hbase.HTableDescriptor
import org.apache.hadoop.hbase.client.HBaseAdmin

tablename = ARGV[0]
REGIONS = ARGV[1].to_i
EXPECTED_AVERAGE_METRICS_PER_DEVICE = 150
EXPECTED_DEVICE_COUNT = 1000
METRICS_PER_REGION = EXPECTED_DEVICE_COUNT * EXPECTED_AVERAGE_METRICS_PER_DEVICE / REGIONS

def boundary_marker(n)
  "%06x" % (METRICS_PER_REGION * n).to_i
end

def convert(marker)
  [marker].pack('H*').to_java_bytes
end

last_marker = boundary_marker(REGIONS - 1)
first_marker = boundary_marker(1)

HBaseAdmin.new(HBaseConfiguration.new).createTable(
  HTableDescriptor.new(tablename),
    convert(first_marker),
    convert(last_marker),
    REGIONS)

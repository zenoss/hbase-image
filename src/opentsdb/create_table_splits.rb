#!/opt/hbase/bin/hbase org.jruby.Main
# usage: ./create_table.rb tsdb f1 255
include Java
import org.apache.hadoop.hbase.HBaseConfiguration
import org.apache.hadoop.hbase.HTableDescriptor
import org.apache.hadoop.hbase.HColumnDescriptor
import org.apache.hadoop.hbase.client.HBaseAdmin

tablename = ARGV[0]
cfname = ARGV[1]
REGIONS = ARGV[2].to_i
print "regions",  REGIONS
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

colDesc = HColumnDescriptor.new(cfname)
tblDesc = HTableDescriptor.new(tablename)
tblDesc.addFamily(colDesc)

HBaseAdmin.new(HBaseConfiguration.new).createTable(
  tblDesc,
    convert(first_marker),
    convert(last_marker),
    REGIONS)

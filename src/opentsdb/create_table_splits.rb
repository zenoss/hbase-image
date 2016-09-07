#!/opt/hbase/bin/hbase org.jruby.Main
# usage: ./create_table.rb tsdb f1
include Java
import org.apache.hadoop.hbase.HBaseConfiguration
import org.apache.hadoop.hbase.HTableDescriptor
import org.apache.hadoop.hbase.HColumnDescriptor
import org.apache.hadoop.hbase.client.HBaseAdmin

tablename = ARGV[0]
cfname = ARGV[1]

def convert(marker)
  [marker].pack('H*').to_java_bytes
end

colDesc = HColumnDescriptor.new(cfname)
tblDesc = HTableDescriptor.new(tablename)
tblDesc.addFamily(colDesc)

# These marker values are used in conjunction with the opentsdb 
# setting "tsd.core.uid.random_metrics=true" in opentsdb.conf.
# These values will help in providing a more even distribution of
# items in each region.
first_marker = "\x00\x00\x01"
last_marker = "\xFF\xFF\xFF"

HBaseAdmin.new(HBaseConfiguration.new).createTable( 
	tblDesc,
    convert(first_marker),
    convert(last_marker),
    256)

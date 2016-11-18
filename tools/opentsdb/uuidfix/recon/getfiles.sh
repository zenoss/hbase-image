#!/bin/bash

ZIPFILETOC=./files_to_tar

for file in $(cat out2/log/failed* | sed 1d)
do
    ls out/err/${file}* >> $ZIPFILETOC
    ls out2/err/${file}* >> $ZIPFILETOC
done

ls out/log/* >> $ZIPFILETOC
ls out2/log/* >> $ZIPFILETOC

for file in *.conf
do
    echo $file >> $ZIPFILETOC
done

tar cvfz out-light.tgz -T $ZIPFILETOC


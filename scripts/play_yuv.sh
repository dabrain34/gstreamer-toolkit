#!/bin/sh
if [ "x$1" == "x" ]
then
echo "Usage: $0 /path/file"
exit 1
fi

FILENAME=$1
WIDTH=$2
HEIGHT=$3
FORMAT=$4
FRAMERATE=$5

if [ -z $GST_LAUNCH ]; then GST_LAUNCH="gst-launch-1.0"; fi
if [ -z $WIDTH ]; then WIDTH=352; fi
if [ -z $HEIGHT ]; then HEIGHT=288; fi
if [ -z $FORMAT ]; then FORMAT=2; fi #2 is I420
if [ -z $FRAMERATE ]; then FRAMERATE="30/1"; fi


$GST_LAUNCH filesrc location=$FILENAME ! rawvideoparse width=$WIDTH height=$HEIGHT format=$FORMAT framerate=$FRAMERATE ! navseek hold-eos=true ! autovideosink

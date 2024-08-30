#!/bin/sh
UNAME=`uname -s`

if [ "x$1" == "x" ]
then
echo "Usage: $0 /path/file"
exit 1
fi

FILENAME=$1



if [ -z $DEMUXER ]; then DEMUXER=qtdemux; fi
if [ -z $PARSER ]; then PARSER=h264parse; fi
if [ -z $OPTS ]; then OPTS=-v; fi
if [ -z $DECODER ]; then PIPEPLINE_TYPE=vah264dec; fi
if [ -z $PIPELINE_TYPE ]; then PIPEPLINE_TYPE=vah264dec; fi
if [ -z $GST_LAUNCH ]; then GST_LAUNCH="gst-launch"; fi
if [ -z $PLAYBIN_ELEMENT ]; then PLAYBIN_ELEMENT="playbin2"; fi
if [ -z $SINK ]; then 
if [ "x$UNAME" == "xDarwin" ]; then
SINK="osxvideosink"; 
else
SINK="autovideosink"; 
fi
fi


if [ "x$2" != "x" ]
then
PIPELINE_TYPE=$2
fi

if [ -z $GST_DEBUG ]; then
export GST_DEBUG="*:2,vtdec*:9, videodeco*:9"
fi

if [ -z $GST_DEBUG_FILE ]; then
export GST_DEBUG_FILE="/tmp/$(basename $FILENAME)_$PIPELINE_TYPE.log"
fi

#SRC_OPTIONS="num-buffers=50"

set -x
case "$PIPELINE_TYPE" in

playbin) echo $TYPE
    $GST_LAUNCH $OPTS $PLAYBIN_ELEMENT uri="file://$FILENAME"
    ;;

full) echo $TYPE
    $GST_LAUNCH $OPTS filesrc location="$FILENAME" $SRC_OPTIONS ! $DEMUXER ! $PARSER ! $DECODER ! $SINK
    ;;
*) echo "Invalid option"
   ;;
esac

#!/bin/sh
UNAME=`uname -s`

if [ "x$1" == "x" ]
then
echo "Usage: $0 /path/file"
exit 1
fi
FILENAME=$1
DEST_FILE=$2


if [ -z $DEMUXER ]; then DEMUXER=qtdemux; fi
if [ -z $PARSER ]; then PARSER=h264parse; fi
if [ -z $OPTS ]; then OPTS=-v; fi
if [ -z $PIPEPLINE_TYPE ]; then PIPEPLINE_TYPE=decodebin-mp3; fi
if [ -z $GST_LAUNCH ]; then GST_LAUNCH="gst-launch-1.0"; fi
if [ -z $DECODEBIN_ELEMENT ]; then DECODEBIN_ELEMENT="decodebin"; fi
if [ -z $ENCODER ]; then ENCODER="flump3enc"; fi
if [ -z $SINK ]; then 
SINK="filesink location=$DEST_FILE"
fi


if [ "x$3" != "x" ]
then
PIPEPLINE_TYPE=$3
fi

if [ -z $GST_DEBUG ]; then
export GST_DEBUG="*:2"
fi

if [ -z $GST_DEBUG_FILE ]; then
export GST_DEBUG_FILE="/tmp/$(basename $FILENAME)_$PIPEPLINE_TYPE.log"
fi

#SRC_OPTIONS="num-buffers=50"

set -x
case "$PIPEPLINE_TYPE" in


decodebin-mp3) echo $TYPE
    $GST_LAUNCH $OPTS filesrc location="$FILENAME" $SRC_OPTIONS ! $DECODEBIN_ELEMENT name=decoder decoder. ! queue ! fakesink decoder. ! queue ! audioconvert ! $ENCODER ! $SINK

    ;;

*) echo "Invalid option"
   ;;
esac



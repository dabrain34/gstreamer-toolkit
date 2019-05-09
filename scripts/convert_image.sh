#!/bin/sh

res=$(which identify)
if [ "x$?" != "x0" ]
then
echo "Install ImageMagick's identify first"
exit 1
fi

if [ "x$1" == "x" ]
then
echo "Usage: $0 /path/file resize_factor_in_percent"
exit 1
fi

FILENAME=$1

if [ "x$2" == "x" ]
then
echo "Usage: $0 /path/file resize_factor_in_percent"
exit 1
fi
RESIZE=$(expr $2)

if [ "x$3" == "x" ]
then
NEW_FILENAME="$FILENAME.jpg"
else
NEW_FILENAME=$3
fi

WIDTH=$(identify -format "%w" "$FILENAME")> /dev/null
HEIGHT=$(identify -format "%h" "$FILENAME")> /dev/null

echo "file $FILENAME sizes $WIDTH X $HEIGHT"

let "NEW_WIDTH= ($RESIZE * $WIDTH) / 100"
let "NEW_HEIGHT= ($RESIZE * $HEIGHT) / 100"

echo "file $FILENAME resizes to $NEW_WIDTH X $NEW_HEIGHT to $NEW_FILENAME"


SRC_EL="filesrc location=$FILENAME"
DECODE_EL="decodebin ! videoconvert"
SCALE_EL="videoscale ! video/x-raw,width=$NEW_WIDTH,height=$NEW_HEIGHT"
ENC_EL="jpegenc"
SINK_EL="filesink location=$NEW_FILENAME"

gst-launch-1.0 -v  $SRC_EL ! $DECODE_EL ! $SCALE_EL  ! $ENC_EL ! $SINK_EL
echo "new file $NEW_FILENAME created with size $NEW_WIDTH X $NEW_HEIGHT"
 
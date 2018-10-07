#!/bin/sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
DIR=`pwd`

#change the for loop separator. Instead of space use linefeed.
IFS=$'\n'

if [ "x$1" != "x" ]; then
    DIR=$1
fi

IFS=$'\n'
FILES=`find $DIR -type f -maxdepth 1`
#echo $FILES
export GST_OPTS="-m"
mkdir $DIR/transcoded
for FILE in $FILES
do
echo $FILE
FILENAME=`basename "$FILE"`
echo $FILENAME
$SCRIPT_DIR/transcode_media.sh $FILE $DIR/transcoded/$FILENAME.mp3
done

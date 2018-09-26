#!/bin/sh

FILES=`find $1 -name "*"`
#echo $FILES
for FILE in $FILES
do
echo $FILE
FILENAME=`basename "$FILE"`
echo $FILENAME
#./transcode_media.sh $FILE $2/$FILENAME.mp3
done

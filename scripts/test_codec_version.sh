#!/bin/sh

if [ "x$CERBERO_PREFIX" == "x" ]
then
echo "Must be run under cerbero shell"
exit 1
fi

function usage() {
    echo "Usage: $0 path_to_codec_binaries_folder plugin(vadec) version(200)"
    exit 1
}





DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
UNAME=`uname -s`
CODEC_BINARIES_FOLDER="/Users/stephane/Documents/DEV/FLUENDO/PLUGINS/codecs-binaries/"
if [ "x$1" != "x" ]
then
CODEC_BINARIES_FOLDER=$1
fi

if [ ! -d $CODEC_BINARIES_FOLDER ]
then
echo "The folder $CODEC_BINARIES_FOLDER does not exist"
usage
exit 1
fi


FLU_PLUGIN=vadec
if [ "x$2" != "x" ]
then
FLU_PLUGIN=$2
fi

TAG_VERSION=200
if [ "x$3" != "x" ]
then
TAG_VERSION=$3
fi

GST_VERSION=0.10
TARGET=osx
ARCH=x86_64
DEMO_VERSION=full
FILENAME=libgstflu$FLU_PLUGIN.so
TAG=gst-fluendo-$FLU_PLUGIN/0.10.$TAG_VERSION/osx/$ARCH/$GST_VERSION/$DEMO_VERSION
FILE=gstreamer-$GST_VERSION/$TARGET/$ARCH/$FILENAME
ALL_TAGS=`GIT_DIR=$CODEC_BINARIES_FOLDER/.git git tag -l | grep gst-fluendo-$FLU_PLUGIN | grep $TARGET | grep $DEMO_VERSION | grep $ARCH | grep "$GST_VERSION0/"`
echo $ALL_TAGS

DEST_FILE="$CERBERO_PREFIX/lib/gstreamer-0.10/$FILENAME"
MEDIA_FILE="/Users/stephane/Movies/martin.mov"
MEDIA_FILE=$(printf %q "$MEDIA_FILE")

set -x
GIT_DIR=$CODEC_BINARIES_FOLDER/.git git checkout master
GIT_DIR=$CODEC_BINARIES_FOLDER/.git git show $TAG:$FILE > $DEST_FILE

if [ "x$UNAME" == "xDarwin" ]
then
$DIR/osx_relocate_lib.sh $DEST_FILE
fi

#$DIR/play_media.sh $MEDIA_FILE

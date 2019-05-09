#!/bin/sh

if [ "x$CERBERO_PREFIX" == "x" ]
then
echo "Must be run under cerbero shell"
exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

export PLAYBIN_ELEMENT=playbin2
export GST_LAUNCH=gst-launch-0.10
export VT_DEC=vtdec_h264

$DIR/play_media.sh $@

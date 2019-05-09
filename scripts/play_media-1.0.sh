#!/bin/sh


DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

export PLAYBIN_ELEMENT=playbin
export GST_LAUNCH=gst-launch-1.0
export VT_DEC=vtdec
export SINK=autovideosink

$DIR/play_media.sh $@

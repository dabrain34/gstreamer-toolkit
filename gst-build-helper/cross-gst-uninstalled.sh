#!/bin/sh

BUILD_DIR=$1
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

if [ -z $BUILD_DIR ]; then
BUILD_DIR=$SCRIPT_DIR/build
fi

prepend()
{
  var=$1
  dir=$2
  current=$(eval echo "\$$var")
  if [ -d "$dir" ]
  then
    msg="Prepend '$dir' to $var"
    if [ -z "$current" ]; then
      eval export $var="$dir"
    elif [ -z "$(echo ":$current:" | grep -e ":$dir:")" ]; then
      eval export $var="$dir:$current"
    else
      msg=
    fi
    if [ -n "$msg" ]; then
      echo "    $msg"
    fi
  else
    echo "$dir does not exist"
  fi
}

set_path()
{
  var=$1
  dir=$2
  current=$(eval echo "\$$var")
  if [ -z $current ]; then
      eval export $var="$dir"
      echo "    Setting $var to '$dir'"
  fi
}

export PS1="[gst]\\u@\\h:\\w\\$"

set_path GST_REGISTRY $BUILD_DIR/registry.dat

prepend PATH $BUILD_DIR/bin/
prepend PATH $BUILD_DIR/usr/bin/
prepend PATH $BUILD_DIR/usr/local/bin

prepend LD_LIBRARY_PATH $BUILD_DIR/lib/
prepend LD_LIBRARY_PATH $BUILD_DIR/usr/lib/
prepend LD_LIBRARY_PATH $BUILD_DIR/usr/local/lib/
prepend LD_LIBRARY_PATH $BUILD_DIR/usr/local/lib/x86_64-linux-gnu/

set_path GST_PLUGIN_PATH $BUILD_DIR/usr/local/lib/gstreamer-1.0
prepend GST_PLUGIN_PATH $BUILD_DIR/usr/local/lib/x86_64-linux-gnu/gstreamer-1.0

set_path GST_OMX_CONFIG_DIR $BUILD_DIR/usr/local/etc/xdg
/bin/sh

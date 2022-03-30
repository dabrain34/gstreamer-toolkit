#!/bin/sh
#
# Check that the code follows a consistant code style
#

# Check for existence of indent, and error out if not present.
# On some *bsd systems the binary seems to be called gnunindent,
# so check for that first.

version=`gnuindent --version 2>/dev/null`
if test "x$version" = "x"; then
  version=`gindent --version 2>/dev/null`
  if test "x$version" = "x"; then
    version=`indent --version 2>/dev/null`
    if test "x$version" = "x"; then
      echo "GStreamer git pre-commit hook:"
      echo "Did not find GNU indent, please install it before continuing."
      exit 1
    else
      INDENT=indent
    fi
  else
    INDENT=gindent
  fi
else
  INDENT=gnuindent
fi

case `$INDENT --version` in
  GNU*)
      ;;
  default)
      echo "GStreamer git pre-commit hook:"
      echo "Did not find GNU indent, please install it before continuing."
      echo "(Found $INDENT, but it doesn't seem to be GNU indent)"
      exit 1
      ;;
esac

INDENT_PARAMETERS="--braces-on-if-line \
	--case-brace-indentation0 \
	--case-indentation2 \
	--braces-after-struct-decl-line \
	--line-length80 \
	--no-tabs \
	--cuddle-else \
	--dont-line-up-parentheses \
	--continuation-indentation4 \
	--honour-newlines \
	--tab-size8 \
	--indent-level2 \
	--leave-preprocessor-space"
path=$1

files=
if [ -d $path ]; then
   echo "$path is a folder, gst-indent will be passed recursively on the folder"
   files=`find $path -regex '.*\.\(c\|cpp\)$' -print`
fi

if [ -f $path ]; then
    echo "$path is a file, gst-indent will be passed on file $file only"
    files=$path
fi

if [ -z $files ]; then 
    echo "no folder or files found. Exit."
    exit 1
fi 

echo "--Checking style--for $path "
for file in $files ; do
    $INDENT ${INDENT_PARAMETERS} \
        $file 2>> /dev/null
    created_file="$file~"
    if [ -f $created_file ];then
        echo "Removing $created_file"
        rm $created_file
    fi
done
echo "--Checking style pass--"

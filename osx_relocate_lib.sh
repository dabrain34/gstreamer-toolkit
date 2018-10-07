#!/bin/sh

UNAME=`uname -s`
set -x 
function relocate_darwin_lib () {
DEST_FILE=$1
LIBRARY_PATH=`otool -L $DEST_FILE | grep glib | sed -e "s/dylib.*/dylib/g" | sed 's/^.//' | sed 's|lib.*|lib|'`
RPATH_LIB=`echo $LIBRARY_PATH | grep '@rpath'`
if [ "x$RPATH_LIB" == "x" ]
then
install_name_tool -add_rpath @loader_path/../../.. $DEST_FILE
install_name_tool -add_rpath @executable_path/../../.. $DEST_FILE
install_name_tool -add_rpath @loader_path/../.. $DEST_FILE
install_name_tool -add_rpath @executable_path/../.. $DEST_FILE
install_name_tool -add_rpath @loader_path/../lib $DEST_FILE
install_name_tool -add_rpath @executable_path/../lib $DEST_FILE
install_name_tool -add_rpath @loader_path/.. $DEST_FILE
install_name_tool -add_rpath @executable_path/.. $DEST_FILE
LIB_FILES=`otool -L $DEST_FILE | grep $LIBRARY_PATH | sed -e "s/dylib.*/dylib/g" | sed 's/^.//'`
#LIB_FILES=`echo $LIB_FILES | tr '\r\n' ' '`

for FILE in $LIB_FILES
do
echo $FILE
NEW_FILE=`echo $FILE | sed 's|.*/lib/|/lib/|'`
echo $NEW_FILE
install_name_tool -change $FILE "@rpath$NEW_FILE" $DEST_FILE
done

fi
}

if [ "x$UNAME" == "xDarwin" ]
then
for FILE in $@
do
relocate_darwin_lib $FILE
done
fi

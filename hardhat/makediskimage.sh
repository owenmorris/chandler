#!/bin/sh

# Convert a directory into a compressed disk image on OSX.  Much thanks to
# Mike Blakeley for the original script.

# Pass a directory name as the one and only argument to the script, and it
# will create a disk image file.

# This line is required if you aren't logged in on the actual Mac console:
# this does not seem to be required in Panther (generates an error)
# disktool -c 0

FOLDER="$1"
if [ -z "$FOLDER" ]; then
echo
echo "usage: $0 <folder>"
echo
exit 1
fi

if [ ! -d "$FOLDER" ]; then
echo $FOLDER does not exist
exit 2
fi

SIZE=`du -s "$FOLDER" | awk '{ print $1 }'`
# allow space for partition map and directory structure
SIZE=`echo 1024 + $SIZE \* 1.1 / 1 | bc`
NAME=`basename "$FOLDER"`
FILE=$NAME.dmg
TMP=${TMP:-/tmp}

if [ $SIZE -lt 9216 ]; then
 SIZE=9216
fi

if [ -e "$FILE" ] ; then
 echo $FILE already exists!
 exit 3
fi

TMPFILE=$TMP/$$.dmg

echo Creating $TMPFILE from $FOLDER, $SIZE sectors...
hdiutil create $TMPFILE -sectors $SIZE -ov
if [ $? -ne 0 ] ; then
 rm -f $TMPFILE
 exit 4
fi
echo

DEVICES=`hdid -nomount $TMPFILE`
DEVMASTER=`echo $DEVICES| awk '{ print $1 }'`
DEVHFS=`echo $DEVICES| awk '{ print $5 }'`
echo Creating HFS partition $NAME on $TMPFILE at $DEVHFS
newfs_hfs -v "$NAME" $DEVHFS
if [ $? -ne 0 ] ; then
 rm -f $TMPFILE
 exit 5
fi
hdiutil eject $DEVMASTER
if [ $? -ne 0 ] ; then
 rm -f $TMPFILE
 exit 6
fi
DEVICES=`hdid $TMPFILE`
if [ $? -ne 0 ] ; then
 rm -f $TMPFILE
exit 7
fi

DEVMASTER=`echo $DEVICES| awk '{ print $1 }'`
DEVHFS=`echo $DEVICES| awk '{ print $5 }'`
echo Copying $FOLDER to /Volumes/$NAME on $DEVMASTER
sudo ditto -rsrcFork "$FOLDER" "/Volumes/$NAME"
if [ $? -ne 0 ]; then
 hdiutil eject $DEVMASTER
 rm -f $TMPFILE
 exit 8
fi

hdiutil eject $DEVMASTER
if [ $? -ne 0 ]; then
 #rm -f $TMPFILE
 exit 9
fi

echo "Compressing $NAME to $FILE"
hdiutil convert $TMPFILE -format UDZO -imagekey zlib-level=9 -o "$FILE"
if [ $? -ne 0 ]; then
 rm -f "$FILE" $TMPFILE
 exit 10
fi

echo "Setting internet-enable flag on"
hdiutil internet-enable -yes "$FILE"
if [ $? -ne 0 ]; then
 rm -f "$FILE" $TMPFILE
 exit 11
fi
rm -f $TMPFILE

# end

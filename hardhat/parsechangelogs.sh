#!/bin/sh

# two arguments:  the starting and ending CVS tags that bookend the date range
# you are interested in (e.g., parsechangelogs.sh CHANDLER_M_01 CHANDLER_M_02)

for file in `find . -name ChangeLog.txt`
do
    echo "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    echo Changes from $file
    cvs diff -r $1 -r $2 -Bbc $file | grep "^\+" | cut --bytes=2-
done

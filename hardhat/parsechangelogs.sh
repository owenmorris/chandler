#!/bin/sh

# cvs diff -r CHANDLER_M_01 -r CHANDLER_M_02 -Bbc `find . -name ChangeLog.txt` | grep "^\+"

for file in `find . -name ChangeLog.txt`
do
    echo "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    echo Changes from $file
    cvs diff -r $1 -r $2 -Bbc $file | grep "^\+" | cut --bytes=2-
done

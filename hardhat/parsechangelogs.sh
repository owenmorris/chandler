#!/bin/sh

for file in `find . -name ChangeLog.txt`
do
    echo "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
    echo Changes from $file
    cvs diff -D $1 -D now -Bbc $file | grep "^\+" | cut --bytes=2-
done

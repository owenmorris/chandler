#!/bin/sh
#-----------------------------------------------------------------------------
#-- Name:        docs/mac/M5converteol.sh
#-- Purpose:     Convert end-of-lines in CodeWarrior exported XML project files
#-- Author:      Gilles Depeyrot
#-- Modified by:
#-- Created:     07.01.2002
#-- RCS-ID:      $Id: M5converteol.sh 5166 2005-04-29 01:36:53Z davids $
#-- Copyright:   (c) 2001 Gilles Depeyrot
#-- Licence:     wxWindows licence
#-----------------------------------------------------------------------------

echo "Searching for xml files..."
files=`find ../.. -name "*.xml" -print`

for f in $files
do
    cat $f | tr '\r' '\n' > $f.new
    if [ "`diff -q $f $f.new`" != "" ] ; then
        mv $f.new $f
        echo "Converted $f"
    else
        rm $f.new
    fi
done

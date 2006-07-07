#!/bin/bash
#   Copyright (c) 2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

cd `dirname $0`
C_DIR=`pwd`
C_DIR=`dirname $C_DIR`

SCAN_DIR=$C_DIR
OUT_FILE=ChandlerXRC.pot
MERGE_FILE=chandler.pot

while getopts "d:o:m:" Option
do
  case $Option in
    d ) SCAN_DIR=$C_DIR"/"$OPTARG;; # d ) SCAN_DIR="../$OPTARG";;
    o ) OUT_FILE=$OPTARG;;
    m ) MERGE_FILE=$OPTARG
    ;;   # DEFAULT
  esac
done

if [ "$OSTYPE" = "cygwin" ]; then
  SCAN_DIR=`cygpath -aw $SCAN_DIR`
  OUT_FILE=`cygpath -aw $OUT_FILE`
  MERGE_FILE=`cygpath -aw $MERGE_FILE`
fi

XRC_FILES=`find $SCAN_DIR -type f -name *.xrc -print`
CPP_FILES=

for item in $XRC_FILES ; do
  XRCNAME=$item
  CPPNAME=`basename $item .xrc`.cpp
  if [ "$OSTYPE" = "cygwin" ]; then
    XRCNAME=`cygpath -aw $XRCNAME`
    CPPNAME=`cygpath -aw $CPPNAME`
  fi
  wxrc -g -o $CPPNAME $XRCNAME
  CPP_FILES="$CPP_FILES $CPPNAME"
done

xgettext -C -a -o $OUT_FILE $CPP_FILES

for item in $XRC_FILES ; do
  rm `basename $item .xrc`.cpp
done

if [ -f $MERGE_FILE ]; then
  msgmerge -o tmp.pot $MERGE_FILE $OUT_FILE
  rm $MERGE_FILE
  mv tmp.pot $MERGE_FILE
else
  echo $MERGE_FILE "does not exist."
fi
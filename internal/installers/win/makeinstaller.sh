#!/bin/sh

#
# This script aids in calling makensis.exe in cygwin
# It's not needed if the build happens in a native
# windows command shell
#

NSI_OPTION="$1"
NSI_PATH="$2"
NSI_FILE="$3"
NSIS_BIN="$4"

if [ -z "$NSI_FILE" ]; then
    echo
    echo "usage: $0 <snap_option> <path to .nsi file> <.nsi file> <nsis binary>"
    echo
    exit 1
fi

cd $NSI_PATH
"$NSIS_BIN" $NSI_OPTION $NSI_FILE


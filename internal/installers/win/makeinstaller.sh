#!/bin/sh

#
# This script aids in calling makensis.exe in cygwin
# It's not needed if the build happens in a native
# windows command shell
#

NSI_PATH="$1"
NSI_FILE="$2"

if [ -z "$NSI_FILE" ]; then
    echo
    echo "usage: $0 <path to .nsi file> <.nsi file>"
    echo
    exit 1
fi

cd $NSI_PATH
makensis $NSI_FILE


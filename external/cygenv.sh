#!/bin/sh
# cygwin script to assign environment variables for MSVC/Chandler New Builds
# assumes msvc has provided 
#
#  markie@osafoundation.org     2004/04/28

# first test looks for VisualStudio 7.1 Common Tools dir (MSVC installs to all users)
if expr "$VS71COMNTOOLSx" = "x"  > /dev/null
then
    echo You do not have MSVS installed for this user
    exit 1
fi

curdir=`pwd`

cd "$VS71COMNTOOLS"
cd ../..
export COMN7="`pwd`"
cd ..; export MSVC="`pwd`"
cd $curdir

export VSINSTALLDIR="$COMN7/IDE"
export VCINSTALLDIR="$MSVC"

DevEnvDir=$VSINSTALLDIR

#echo DevEnvDir is $DevEnvDir
#
# Root of Visual C++ installed files.
#
MSVCDir=$VCINSTALLDIR/VC7

export PATH="$DevEnvDir":"$MSVCDir/BIN":"$VS71COMNTOOLS":"$VS71COMNTOOLS/bin/prerelease":"$VS71COMNTOOLS/bin":"$PATH"
export INCLUDE="$MSVCDir/ATLMFC/INCLUDE":"$MSVCDir/INCLUDE":"$MSVCDir/PlatformSDK/include/prerelease":"$MSVCDir"/PlatformSDK/include:"$INCLUDE"
export LIB="$MSVCDir/ATLMFC/LIB":"$MSVCDir/LIB":"$MSVCDir/PlatformSDK/lib/prerelease":"$MSVCDir/PlatformSDK/lib":"$LIB"


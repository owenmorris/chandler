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
#echo $curdir

cd "$VS71COMNTOOLS"
#echo VS71COMNTOOLS is `pwd`
cd ../..
#echo parent of VS71COMNTOOLS is `pwd`
export COMN7="`pwd`"
#echo COMN7= $COMN7
cd ..; export MSVC="`pwd`"
cd $curdir
#echo Back in `pwd`

#echo MSVC is $MSVC
export VSINSTALLDIR="$COMN7/IDE"
#echo VSINSTALLDIR is $VSINSTALLDIR
export VCINSTALLDIR="$MSVC"
#echo VCINSTALLDIR is $VCINSTALLDIR

DevEnvDir=$VSINSTALLDIR

#echo DevEnvDir is $DevEnvDir
#
# Root of Visual C++ installed files.
#
MSVCDir=$VCINSTALLDIR/VC7
#echo MSVCDir is $MSVCDir

export PATH="$DevEnvDir":"$MSVCDir"/BIN:"$VS71COMNTOOLS":"$VS71COMNTOOLS"/bin/prerelease:"$VS71COMNTOOLS"/bin:$PATH
#echo PATH is $PATH
export INCLUDE="$MSVCDir"/ATLMFC/INCLUDE:"$MSVCDir"/INCLUDE:"$MSVCDir"/PlatformSDK/include/prerelease:"$MSVCDir"/PlatformSDK/include:$INCLUDE
#echo INCLUDE is $INCLUDE
export LIB="$MSVCDir"/ATLMFC/LIB:"$MSVCDir"/LIB:"$MSVCDir"/PlatformSDK/lib/prerelease:"$MSVCDir"/PlatformSDK/lib:$LIB
#echo LIB is $LIB


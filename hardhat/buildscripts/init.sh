#!/bin/sh

echo $BUILD_ROOT
echo $GCJ_HOME
echo $DEBUG
pwd

cd $BUILD_ROOT

make expand
make $DEBUG 
make $DEBUG binaries

echo Done shell script

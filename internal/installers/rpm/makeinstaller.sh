#!/bin/sh

#
# This script set's up the RPM environment needed
#
# Remember to update the SPEC_VERSION variable when changing the .spec file
# yes, yes, it's an ugly hack but it's working for now
#

SPEC_PATH="$1"
SPEC_FILE="$2"
DISTRIB_PATH="$3"
DISTRIB_FILE="$4"

RPM_PATH=$HOME/rpm
SPEC_VERSION=0.4-8

if [ -z "$DISTRIB_FILE" ]; then
    echo
    echo "usage: $0 <path to .spec file> <.spec file> <path to distrib directory> <distrib file root>"
    echo 
    echo "example: $0 /home/builder/tinderbuild/internal/installers/rpm/ chandler.spec /home/builder/tinderbuild/ Chandler_linux_foo"
    echo
    exit 1
fi

if [ -d "$RPM_PATH/BUILD" ]; then
    echo "Preparing build tree"
    if [ -d "$RPM_PATH/BUILD/OSAF" ]; then
        rm -rf $RPM_PATH/BUILD/OSAF
    fi
    mkdir $RPM_PATH/BUILD/OSAF
    mkdir $RPM_PATH/BUILD/OSAF/usr
    mkdir $RPM_PATH/BUILD/OSAF/usr/local
    cd $RPM_PATH/BUILD/OSAF/usr/local
    echo "Creating build tree from distribution tarball"
    tar xzf $DISTRIB_PATH/$DISTRIB_FILE.tar.gz
    mv $DISTRIB_FILE Chandler
    echo "Ensuring all files have a+r set"
    chmod -R a+r $RPM_PATH/BUILD/OSAF/usr/local/Chandler/
    cd $SPEC_PATH
    echo "Calling rpm -ba $SPEC_FILE"
    rpmbuild -ba $SPEC_FILE
    echo "Moving $RPM_PATH/RPMS/i386/Chandler-$SPEC_VERSION.i386.rpm to $DISTRIB_PATH/$DISTRIB_FILE.i386.rpm"
    mv $RPM_PATH/RPMS/i386/Chandler-$SPEC_VERSION.i386.rpm $DISTRIB_PATH/$DISTRIB_FILE.i386.rpm
    echo "Clearing build tree"
    rm -rf $RPM_PATH/BUILD/OSAF
    echo "rpm generation done"
else
    echo "ERROR: RPM local environment does not seem to be setup"
    exit 1
fi

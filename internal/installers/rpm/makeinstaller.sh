#!/bin/sh

#
# This script set's up the RPM environment needed
#

SPEC_PATH="$1"
SPEC_FILE="$2"
DISTRIB_PATH="$3"
DISTRIB_FILE="$4"
export DISTRIB_VERSION="$5"
export DISTRIB_RELEASE="$6"

RPM_PATH=$HOME/rpm

if [ -z "$DISTRIB_RELEASE" ]; then
    echo
    echo "usage: $0 <path to .spec file> <.spec file> <path to distrib directory> <distrib file root> <major.minor> <release>"
    echo 
    echo "example: $0 /home/builder/tinderbuild/internal/installers/rpm/ chandler.spec /home/builder/tinderbuild/ Chandler_linux_foo 0.4 8"
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
    mv $DISTRIB_FILE chandler
    echo "Ensuring all files have a+r set"
    chmod -R a+r $RPM_PATH/BUILD/OSAF/usr/local/chandler/
    cd $SPEC_PATH
    echo "Calling rpm -ba $SPEC_FILE"
    rpmbuild -ba $SPEC_FILE
    echo "Moving $RPM_PATH/RPMS/i386/Chandler-$DISTRIB_VERSION-$DISTRIB_RELEASE.i386.rpm to $DISTRIB_PATH/$DISTRIB_FILE.i386.rpm"
    mv $RPM_PATH/RPMS/i386/Chandler-$DISTRIB_VERSION-$DISTRIB_RELEASE.i386.rpm $DISTRIB_PATH/$DISTRIB_FILE.i386.rpm
    echo "Clearing build tree"
    rm -rf $RPM_PATH/BUILD/OSAF
    echo "rpm generation done"
else
    echo "ERROR: RPM local environment does not seem to be setup"
    exit 1
fi

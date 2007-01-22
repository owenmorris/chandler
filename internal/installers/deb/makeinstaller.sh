#!/bin/sh

#
# This script set's up the DEB environment needed
#

DEB_PATH="$1"
DISTRIB_PATH="$2"
DISTRIB_FILE="$3"
DISTRIB_VERSION="$4"
DISTRIB_RELEASE="$5"

if [ -z "$DISTRIB_RELEASE" ]; then
    echo
    echo "usage: $0 <path to deb installer> <path to distrib directory> <distrib file root> <major.minor> <release>"
    echo 
    echo "example: $0 /home/builder/tinderbuild/internal/installers/deb/ /home/builder/tinderbuild/ Chandler_linux_foo 0.4 8"
    echo
    exit 1
fi

if [ -d "$DEB_PATH" ]; then
    echo "Clearing debian chandler working image"
    if [ -d "$DEB_PATH/chandler" ]; then
        rm -rf $DEB_PATH/chandler
    fi
    rm -f $DEB_PATH/chandler_*.deb
    echo "Preparing build tree"
    cd $DEB_PATH
    mkdir -p chandler/usr/local
    mkdir chandler/DEBIAN/
    echo "Creating build tree from distribution tarball"
    tar xzf $DISTRIB_PATH/$DISTRIB_FILE.tar.gz
    mv $DISTRIB_FILE chandler/usr/local/chandler
    echo "Ensuring all files have a+r set"
    chmod -R a+r chandler/usr/local/chandler/
    CHANDLER_SIZE=`du -c -b $DEB_PATH/chandler/usr/local/chandler | tail -n1 | awk '{ print $1 }'`
    sed -e "s/CHANDLER_VERSION/$DISTRIB_VERSION.$DISTRIB_RELEASE/" -e "s/CHANDLER_SIZE/$CHANDLER_SIZE/" < $DEB_PATH/control.in > $DEB_PATH/chandler/DEBIAN/control
    echo `pwd`
    echo "Calling dpkg-deb -b chandler chandler_$DISTRIB_VERSION.$DISTRIB_RELEASE-1_i386.deb"
    dpkg-deb -b chandler chandler_$DISTRIB_VERSION.$DISTRIB_RELEASE-1_i386.deb
    echo "Moving .deb to $DISTRIB_PATH/chandler_$DISTRIB_VERSION.$DISTRIB_RELEASE-1_i386.deb"
    mv $DEB_PATH/chandler_$DISTRIB_VERSION.$DISTRIB_RELEASE-1_i386.deb $DISTRIB_PATH/$DISTRIB_FILE_i386.deb
    echo "deb generation done"
else
    echo "ERROR: debian local environment does not seem to be setup"
    exit 1
fi

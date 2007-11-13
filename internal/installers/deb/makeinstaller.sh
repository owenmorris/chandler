#!/bin/sh

#
# This script set's up the DEB environment needed
#

DEB_PATH="$1"
DISTRIB_PATH="$2"
DISTRIB_FILE="$3"
DISTRIB_VERSION="$4"
DISTRIB_MODE="$5"
DISTRIB_RELEASE="1"

if [ -z "$DISTRIB_MODE" ]; then
    echo
    echo "usage: $0 <path to deb installer> <path to distrib directory> <distrib file root> <major.minor> <mode>"
    echo 
    echo "example: $0 /home/builder/tinderbuild/internal/installers/deb/ /home/builder/tinderbuild/ Chandler_linux_foo 0.4 debug"
    echo
    exit 1
fi

if [ "$DISTRIB_MODE" = "release" ]; then
  DISTRIB_MODE="_"
else
  DISTRIB_MODE="_${DISTRIB_MODE}_"
fi

if [ -d "$DEB_PATH" ]; then
    echo "Clearing debian chandler working image"
    if [ -d "{$DEB_PATH}/chandler" ]; then
        rm -rf ${DEB_PATH}/chandler
    fi
    rm -f ${DEB_PATH}/chandler_*.deb
    echo "Preparing build tree"
    cd ${DEB_PATH}
    if [ -d chandler ]; then
        rm -rf chandler
    fi
    
    echo "Creating man page"
    mkdir -p chandler/usr/share/man/man1
    cat ${DISTRIB_PATH}/chandler/distrib/linux/chandler.1 | sed "s/CHANDLER_VERSION/${DISTRIB_VERSION}-${DISTRIB_RELEASE}/" > chandler/usr/share/man/man1/chandler.1
    gzip -9 chandler/usr/share/man/man1/chandler.1
    
    mkdir -p chandler/usr/local
    mkdir chandler/DEBIAN/
    cd chandler/usr/local
    
    echo "Creating build tree from distribution files"
    if [ -f ${DISTRIB_PATH}/${DISTRIB_FILE}.tar.gz ]; then
        tar xzf ${DISTRIB_PATH}/${DISTRIB_FILE}.tar.gz
        mv ${DISTRIB_FILE} chandler
    else
        cp -a ${DISTRIB_PATH}/${DISTRIB_FILE} chandler
    fi
    
    echo "Ensuring all files have a+r set"
    chmod -R a+r chandler/
    cd ${DEB_PATH}
    CHANDLER_SIZE=`du -c -b ${DEB_PATH}/chandler/usr/local/chandler | tail -n1 | awk '{ print $1 }'`
    sed -e "s/CHANDLER_VERSION/${DISTRIB_VERSION}-${DISTRIB_RELEASE}/" -e "s/CHANDLER_SIZE/${CHANDLER_SIZE}/" < ${DEB_PATH}/control.in > ${DEB_PATH}/chandler/DEBIAN/control
    echo `pwd`
    echo "Calling dpkg-deb -b chandler chandler_${DISTRIB_VERSION}-${DISTRIB_RELEASE}_i386.deb"
    dpkg-deb -b chandler chandler_${DISTRIB_VERSION}-${DISTRIB_RELEASE}_i386.deb
    echo "Moving ${DEB_PATH}/chandler_${DISTRIB_VERSION}-${DISTRIB_RELEASE}_i386.deb to ${DISTRIB_PATH}/Chandler_linux${DISTRIB_MODE}${DISTRIB_VERSION}-${DISTRIB_RELEASE}_i386.deb"
    mv ${DEB_PATH}/chandler_${DISTRIB_VERSION}-${DISTRIB_RELEASE}_i386.deb ${DISTRIB_PATH}/Chandler_linux${DISTRIB_MODE}${DISTRIB_VERSION}-${DISTRIB_RELEASE}_i386.deb
    echo "deb generation done"
else
    echo "ERROR: debian local environment does not seem to be setup"
    exit 1
fi

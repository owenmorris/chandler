#!/bin/sh
#		Install Chandler
#
#		version 0.3 of 3/23/2004

VERSION=0.3-1

me=`echo "$0" | sed -e 's,.*/,,'`

usage="\
Usage: $0 [OPTION]

Install Chandler on Linux.

Operation modes:
  -h, --help         print this help, then exit
  -d, --debug        install debug
  -r, --release      install release"

help="
Try \`$me --help' for more information."

case $# in
 0) echo "Build debug or release: -d or -r" >&2
    exit 1;;
 1) ;;
 *) echo "$me: too many arguments$help" >&2
    exit 1;;
esac

	if ! test -d osaf; then
		echo "Getting Chandler source"
		echo "(type anonymous after the following prompt)"
		cvs -d :pserver:anonymous@cvs.osafoundation.org:/usr/local/cvsrep login
		cvs -d :pserver:anonymous@cvs.osafoundation.org:/usr/local/cvsrep co chandler-app
	else
		echo "Source already checked out"
	fi

	case $1 in
    --debug | --de* | -d )
      if test -d osaf/chandler/debug; then
        echo "Debug build exists; archiving it"
        mv osaf/chandler/debug/ debug-`date +%Y%m%d-%H%M`
      fi
	  if ! test -f debug-$VERSION.tar.gz; then 
		echo "Getting debug tarball"
		curl -O http://builds.o11n.org/external/linux/debug-$VERSION.tar.gz
	  fi
		echo "Expanding tarball"
		tar -C osaf/chandler/ -xzf debug-$VERSION.tar.gz
		dashd="-d"
	;;
    --release | --re* | -r )
      if test -d osaf/chandler/release; then
        echo "Release build exists; archiving it"
        mv osaf/chandler/release/ release-`date +%Y%m%d-%H%M`
      fi
	  if ! test -f release-$VERSION.tar.gz; then 
		echo "Getting release tarball"
		curl -O http://builds.o11n.org/external/linux/release-$VERSION.tar.gz
	  fi
		echo "Expanding tarball"
		tar -C osaf/chandler/ -xzf release-$VERSION.tar.gz
		dashd=
	;;
    --help | --h* | -h )
       echo "$usage"; exit 0 ;;
	esac
	
	echo "Finalizing Installation"
	cd osaf/chandler/Chandler/repository
	../../../hardhat/hardhat.py $dashd -b
	cd ..
	../../hardhat/hardhat.py $dashd -b
	echo "Ready to run - type cd osaf/chandler/Chandler"
	echo "   then"
	echo "               type ../../hardhat/hardhat.py $dashd -x"

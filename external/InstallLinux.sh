#!/bin/sh
#		Install Chandler
#
#		version 0.3.3 of 4/28/2004

VERSION=0.3-3

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
 0) echo "$me --debug | --release | -d | -r  ?" >&2
    exit 1;;
 1) ;;
 *) echo "$me: too many arguments$help" >&2
    exit 1;;
esac

    echo "Install and startup Chandler developer distribution"
    
	if ! test -d chandler; then
		echo "Getting Chandler from cvs"
		if test -f ~/.cvspass; then
			echo -c
		else
    		echo "(type anonymous after the following prompt)"
            cvs -d :pserver:anonymous@cvs.osafoundation.org:/usr/local/cvsrep login
		fi
		cvs -d :pserver:anonymous@cvs.osafoundation.org:/usr/local/cvsrep -q co chandler hardhat Makefile
	else
		echo "Source already checked out"
	fi

	case $1 in
    --debug | --de* | -d )
		if test -d debug; then
			echo "Previous debug build exists; archiving it"
			mv debug/ debug-`date +%Y%m%d-%H%M`
		fi
		bigD="DEBUG=1"
		smallD="-d"
		releaseDir="debug"
	;;
    --release | --re* | -r )
		if test -d release; then
			echo "Previous release build exists; archiving it"
			mv release/ release-`date +%Y%m%d-%H%M`
		fi
		bigD=""
		smallD=""
		releaseDir="release"
	;;
    --help | --h* | -h )
       echo "$usage"; exit 0 ;;
	esac

	echo "Installing chandler"
	make $bigD install
	echo "Finalizing Installation"
	cd chandler
	../hardhat/hardhat.py $smallD -b
	
	echo "Starting up ..."
	../$releaseDir/RunRelease -stderr -create

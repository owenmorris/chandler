README
======

$ cd internal/installers/deb
$ mv /path/to/the/chandler/dir usr/lib/chandler

Edit the DEBIAN/control file to contain the correct version and size.

Build the .deb, substituting the correct version number:

$ dpkg-deb -b chandler chandler_0.7alpha5.dev+r0000+00000000000000-1_i386.deb

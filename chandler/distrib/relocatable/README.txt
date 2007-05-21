
Do not run the Makefile in this directory directly but instead connect to
your chandler development directory and run 'make relocatable-distro'.

This directory contains the files necessary to create a self-contained,
relocatable Chandler distribution. Such a distribution can be installed and
run from a removable deployment device such as a USB key, a portable
hard drive, an iPod, etc...

It is recommended to have at least 1 GB of free space available on the
deployment device: 350 MB to unpack the archive being produced here and the
rest for the three Berkeley DB environments that will be created when
Chandler is first run on each platform.

The deployment device should be formatted with a file system supported by
all the operating systems it is going to be used with. For example, FAT32 is
supported by Mac OS X, Linux and Windows.

The relocatable distribution is created inside your chandler development
tree in a directory called 'relocatable'. The process checks out a clean
chandler tree based on the same svn url you're currently using, downloads
the binary archives as needed for the three platforms and installs them into
this directory. When the process completes, you have a chandler.tar.bz2
archive you can unpack on the deployment device of your choice.

The deployment tar archive contains one directory tree rooted at 'chandler'
that contains a chandler python tree and three i386-based executable trees
for Mac OS X, Ubuntu Linux and Windows.

In the root chandler directory there are three starter applications,
Chandler.app for Mac OS X, chandler.sh for Linux and chandler.bat for
Windows that start Chandler for their respective platform.

The repository data and transactional log files are shared among these three
Chandler implementation. Because of endianness constraints for sharing
transactional log files, this distribution is not supported on Power-PC chips.

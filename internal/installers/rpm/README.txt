#
# Chandler RPM Installer README.txt
#
# $Revision$
# $Date$
# Copyright (c) 2004 Open Source Applications Founation
# http://osafoundation.org/Chandler_0.1_license_terms.htm
#

To build the binary RPM, you need to do the following:

First, create a rpm build environment that will let you test
and install into something other than your actual root directories.

  1.  create a rpm build environment:
      
      cd ~
      mkdir rpm
      mkdir rpm/BUILD
      mkdir rpm/SOURCES
      mkdir rpm/SPECS
      mkdir rpm/SRPMS
      mkdir rpm/RPMS
      mkdir rpm/RPMS/i386
        
  2.  create a ~/.rpmmacros file that contains the following:
  
      %_topdir /home/whatever_user_name_where_rpm_lives/rpm

After you have setup the RPM environment, you can create the RPM by
running the makeinstaller.sh helper script.  This script is what is
run within the Hardhat/Tinderbox environment so it has some assumptions.

Running internal/installers/rpm/makeinstaller.sh without any command
line parameters will give you the following usage help:

   usage: $0 <path to .spec file> <.spec file> <path to distrib directory> <distrib file root>

   example: $0 /home/builder/tinderbuild/internal/installers/rpm/ chandler.spec /home/builder/tinderbuild/ Chandler_linux_foo
   
This script will check the rpm setup, copy the distribution tarball from 
the tinderbuild working directory, setup the proper SOURCES/ tree, call
rpmbuild and then finally copy and rename the rpm to the tinderbuild 
working directory.


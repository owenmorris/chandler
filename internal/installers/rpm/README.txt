#
# Chandler RPM Installer README.txt
#
# $Revision$
# $Date$
# Copyright (c) 2004 Open Source Applications Founation
# http://osafoundation.org/Chandler_0.1_license_terms.htm
#

NOTE:  This is a test RPM - it has been tested only on a basic 
       FC2 setup and has not been tested to ensure a clean
       un-install
       
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

  3. create a temp dir to extract and "massage" the chandler distribution
      
      mkdir osaf_temp 

Once the above is ready, then you can retrieve the distribution tarball
you want to build the binary RPM from and prepare it.  These steps will
very soon be scripted so that they are done by the hardhat and/or tinderbox
scripts.
  
  1.  cd /path/to/osaf_temp
  2.  mkdir usr
      mkdir usr/local
  3.  cd usr/local
  4.  tar xvzf Chandler_debug_foo.tar.gz
  5.  cd ../..
  6.  tar zcvf ~/rpm/SOURCES/chandler.tar.gz usr
  
Note that currently the chandler.spec file has a number of hard-coded 
entries.  The plan is to replace them with references to defines that
are created by a wrapper script.

Once the SOURCES tarball is created, now it's time to tell rpmbuild to
do it's thing.
  
  rpmbuild -ba chandler.spec
  
Note that you will see a number of dependency errors - these are expected
at this stage.
  
After rpmbuild runs, you will find a binary RPM in ~/rpm/RPMS/i386/ that
is named Chandler-0.4-1.i386.rpm

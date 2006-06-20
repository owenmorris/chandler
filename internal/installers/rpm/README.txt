#
# Chandler RPM Installer README.txt
#
#   Copyright (c) 2004-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


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

   usage: $0 <path to .spec file> <.spec file> <path to distrib directory> <distrib file root> <major.minor> <release>

   example: $0 /home/builder/tinderbuild/internal/installers/rpm/ chandler.spec /home/builder/tinderbuild/ Chandler_linux_foo 0.4 8
   
This script will check the rpm setup, copy the distribution tarball from 
the tinderbuild working directory, setup the proper SOURCES/ tree, call
rpmbuild and then finally copy and rename the rpm to the tinderbuild 
working directory.

If you do need to run rpmbuild manually, read the contents of 
makeinstallers.sh to see what needs to be done for rpmbuild to work.

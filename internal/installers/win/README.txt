#
# Chandler Win32 Installer README.txt
#
# $Revision$
# $Date$
# Copyright (c) 2004,2005 Open Source Applications Founation
# http://osafoundation.org/Chandler_0.1_license_terms.htm
#

Currently the windows installation tool (Setup.exe) is created using
the NSIS (Nullsoft Scriptable Install System) which can be found at 
http://nsis.sourceforge.net/ 

Version 2.02 is currently being used (nsis202.exe) and no additional
third-part scripts are required.  That will soon change as more
features are added, network downloading/updating for instance.

Compiling setup.exe under Windows

  NOTE: if you are running the build process under Cygwin,
        there is a helper script in internal/installers/win
        called makeinstallers.sh that checks the setup, calls
        makensis and then copies and renames Setup.exe to the
        tinderbuild working directory.

  1.  create an installation image of Chandler in a build directory
  2.  place in the build directory the chandler.nsi script
  3.  change to the build directory
  4.  run makensis:
  
      \path\to\nsis\makensis chandler.nsi
      
  5.  the Setup.exe will be created in the build directory

Compiling setup.exe under Linux

  1.  create an installation image of Chandler in a build directory
  2.  place in the build directory the chandler.nsi script
  3.  change to the build directory
  4.  run makesys:
  
      /path/to/makesys chandler.nsi
  
  5.  the Setup.exe will created in the build directory

Installing NSIS on Linux

  1.  extract the nsis204.tar.bz2 tarball
  2.  cd NSIS/Source
  3.  run "make USE_PRECOMPILED_EXEHEADS=1"
  4.  cd ..
  5.  run "./install.sh /prefix/path/"
  
  This will create a nsis/ install directory and the makesys binary
  will be found in nsis/bin/
  
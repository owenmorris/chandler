#
# Chandler Win32 Installer README.txt
#
# $Revision$
# $Date$
# Copyright (c) 2004 Open Source Applications Founation
# http://osafoundation.org/Chandler_0.1_license_terms.htm
#

Currently the windows installation tool (Setup.exe) is created using
the NSIS (Nullsoft Scriptable Install System) which can be found at 
http://nsis.sourceforge.net/ 

Version 2.02 is currently being used (nsis202.exe) and no additional
third-part scripts are required.  That will soon change as more
features are added, network downloading/updating for instance.

To build the install tool, you need to do the following steps:

  1.  create an installation image of Chandler in a build directory
  2.  place in the build directory the chandler.nsi script
  3.  change to the build directory
  4.  run makensis:
  
      \path\to\nsis\makensis chandler.nsi
      
  5.  the Setup.exe will be created in the build directory

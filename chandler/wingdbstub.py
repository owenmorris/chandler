#########################################################################
""" wingdbstub.py    -- Debug stub for debuggifying Python programs

Copyright (c) 1999-2001, Archaeopteryx Software, Inc.  All rights reserved.

Written by Stephan R.A. Deibel and John P. Ehresman

Usage:
-----

This is the file that Wing DB users copy into their python project 
directory if they want to be able to debug programs that are launched
outside of the IDE (e.g., CGI scripts, in response to a browser page
load).

To use this, edit the configuration values below to match your 
Wing IDE installation and requirements of your project.

Then, add the following line to your code:

  import wingdbstub

Debugging will start immediately after this import statements.

Next make sure that your IDE is running and that it's configured
to do passive listening and accept passive connections from the
host the debug program will be running on.

Now, invoking your python file should run the code within the debugger.
Note, however, that Wing will not stop in the code unless a breakpoint
set set.

If the debug process is started before the IDE, or is not listening
at the time this module is imported then the program will run with
debugging until an attach request is seen.  Attaching only works 
if the .wingdebugpw file is present; see the manual for details.

One win32, you either need to edit WINGHOME in this script or
pass in an environment variable called WINGHOME that points to
the Wing IDE installation directory.

"""
#########################################################################

import sys
import os
import string
import imp


#------------------------------------------------------------------------
# Default configuration values:  Note that the named environment 
# variables, if set, will override these settings.

# Set this to 1 to disable all debugging; 0 to enable debugging
# (WINGDB_DISABLED environment variable)
kWingDebugDisabled = 0

# Host:port of the IDE within which to debug: As configured in the IDE
# with the Server Port preference
# (WINGDB_HOSTPORT environment variable)
kWingHostPort = 'localhost:50005'

# Port on which to listen for connection requests, so that the
# IDE can (re)attach to the debug process after it has started
# This is only used when the debug process is not attached to
# an IDE or the IDE has dropped its connection. The configured
# port can optionally be added to the IDE's Common Attach Hosts
# preference. Note that a random port is used instead if this 
# port is already in use!
# (WINGDB_ATTACHPORT environment variable)
kAttachPort = '50015'

# Set this to a filename to log verbose information about the debugger
# internals to a file.  If the file does not exist, it will be created
# as long as its enclosing directory exists and is writeable.  Use 
# "<stderr>" or "<stdout>".  Note that "<stderr>" may cause problems 
# on win32 if the debug process is not running in a console.
# (WINGDB_LOGFILE environment variable)
kLogFile = None

# Set this to 1 when debugging embedded scripts:  It turns off
# automatic detecting of program quit so that the debug session
# can span multiple script invocations.
# (WINGDB_EMBEDDED environment variable)
kEmbedded = 0

# Path to search for the debug password file and the name of the file
# to use.  The password file contains the encryption type and connect 
# password for all connections to the IDE and must match the .wingdebugpw
# file in the profile dir used by the IDE.  Any entry of '$<winguserprofile>' 
# is replaced by the wing user profile directory for the user that the 
# current process is running as
# (WINGDB_PWFILEPATH environment variable)
kPWFilePath = [os.path.dirname(__file__), '$<winguserprofile>']
kPWFileName = '.wingdebugpw'

# Whether to exit if the debugger fails to run or to connect with an IDE
# for whatever reason
kExitOnFailure = 0

#------------------------------------------------------------------------
# Find Wing debugger installation location

# Edit this to point to your Wing installation or comment out to use env setting
WINGHOME = r"C:\Program Files\Wing IDE 2.1"

# Check environment:  Must have WINGHOME defined if still == None
if WINGHOME == None:
  if os.environ.has_key('WINGHOME'):
    WINGHOME=os.environ['WINGHOME']
  else:
    print "*******************************************************************"
    print "Error: Could not find Wing installation!  You must set WINGHOME or edit"
    print "wingdbstub.py where indicated to point it to the location where"
    print "Wing IDE is installed."
    sys.exit(1)


#------------------------------------------------------------------------
# Sanity check:  Debugging in optimized mode makes no sense
if __debug__ == 0:
  print "*******************************************************************"
  print "Error: Cannot run a debug process with optimized python because"
  print "Error: this omits necessary debug information from byte code."
  print "Error: You must omit the -O or -OO command line option, or undefine"
  print "Error: environment variable PYTHONOPTIMIZE before launching python."
  sys.exit(2)
  
#------------------------------------------------------------------------
# Start debugging if not disabled and this module has never been imported
# before
if not os.environ.has_key('WINGDB_ACTIVE'):
  debugger = None
if not kWingDebugDisabled and not os.environ.has_key('WINGDB_DISABLED') and \
   not os.environ.has_key('WINGDB_ACTIVE'):

  exit_on_fail = 0
  
  try:
    # Obtain exit if fails value
    exit_on_fail = os.environ.get('WINGDB_EXITONFAILURE', kExitOnFailure)
    
    # Obtain configuration for log file to use, if any
    logfile = os.environ.get('WINGDB_LOGFILE', kLogFile)
    if logfile == '-' or logfile == None or len(string.strip(logfile)) == 0:
      logfile = None
  
    # Determine remote host/port where the IDE is running
    hostport = os.environ.get('WINGDB_HOSTPORT', kWingHostPort)
    colonpos = string.find(hostport, ':')
    host = hostport[:colonpos]
    port = int(hostport[colonpos+1:])
  
    # Determine port to listen on locally for attach requests
    attachport = int(os.environ.get('WINGDB_ATTACHPORT', kAttachPort))
  
    # Check if running embedded script
    embedded = int(os.environ.get('WINGDB_EMBEDDED', kEmbedded))
  
    # Obtain debug password file search path
    if os.environ.has_key('WINGDB_PWFILEPATH'):
      pwfile_path = string.split(os.environ['WINGDB_PWFILEPATH'],
                                 os.pathsep)
    else:
      pwfile_path = kPWFilePath
    
    # Obtain debug password file name
    if os.environ.has_key('WINGDB_PWFILENAME'):
      pwfile_name = os.environ['WINGDB_PWFILENAME']
    else:
      pwfile_name = kPWFileName
    
    # Load wingdb.py
    wingdb = None
    for path in (os.path.join(WINGHOME, 'bin'), os.path.join(WINGHOME, 'src')):
      try:
        f, p, d = imp.find_module('wingdb', [path])
        try:
          wingdb = imp.load_module('wingdb', f, p, d)
        finally:
          if f is not None:
            f.close()
        break
      except ImportError:
        pass
    if wingdb == None:
      print "*******************************************************************"
      print "Error: Cannot find wingdb.py in $(WINGHOME)/bin or $(WINGHOME)/src"
      print "Error: Please check the WINGHOME definition in wingdbstub.py"
      sys.exit(2)
    
    # Find the netserver module and create an error stream
    netserver = wingdb.FindNetServerModule(WINGHOME)
    err = wingdb.CreateErrStream(netserver, logfile)
    
    # Start debugging
    debugger = netserver.CNetworkServer(host, port, attachport, err, 
                                        pwfile_path=pwfile_path,
                                        pwfile_name=pwfile_name)
    debugger.StartDebug(stophere=0, autoquit=not embedded)
    os.environ['WINGDB_ACTIVE'] = "1"
    if debugger.ChannelClosed():
      raise ValueError('Not connected')
    
  except:
    if exit_on_fail:
      raise
    else:
      pass

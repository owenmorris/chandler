__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
  Globals variables

  Initialized by Application, which must be created before they can be used.
Don't add to the globals without reviewing the addition.
"""

from repository.util.Path import Path


chandlerDirectory = None      # Directory containing chandler executable
parcelManager = None          # parcelManager
wxApplication = None          # The application object. Use wx.GetApp() as the prefered
                              # way to get the application object when possible
repository = None             # The repository -- rarely used
                              # Most code should use wx.GetApp() or Globals.wxApplication to
                              # get the wxApplication object it has an instance variable
                              # UIRepositoryView which can be used for many purposes.
mainViewRoot = None           # The main View
views = []                    # A list of nested views
crypto = None                 # Cryptographic services
wakeupCaller = None           # WakeupCaller Service
options = None                # Command line options
args = None                   # Command line arguments

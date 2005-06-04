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
wxApplication = None          # The application object. Use wx.GetApp() as the prefered
                              # way to get the application object when possible.
mainViewRoot = None           # The main View
views = []                    # A list of nested views
wakeupCaller = None           # WakeupCaller Service
mailService = None            # Mail Service (IMAP, POP, SMTP)
options = None                # Command line options
args = None                   # Command line arguments

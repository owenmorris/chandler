__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
  Globals variables

  Initialized by Application, which must be created before they can be used.
Don't add to the globals without reviewing the addition. 
"""

# Used only by application (the old version), so should go away.
application = None            # The wxApplication object
wxMainFrame = None            # Active wxChandlerWindow

association = {}              # A dictionary mapping persistent object ids
                              #    to non-persistent wxPython counterparts
agentManager = None           # AgentManager
chandlerDirectory = None      # Directory containing chandler executable
jabberClient = None           # State of jabber client including presence dictionary
notificationManager = None    # NotificationManager
repository = None             # The repository
mainView = None               # The main View
wxApplication = None          # The wxWindows application object



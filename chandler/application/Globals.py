__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
  Globals variables

  Initialized by Application, which must be created before they can be used.
Don't add to the globals without reviewing the addition.
"""

from repository.util.Path import Path


taskManager = None            # TaskManager
chandlerDirectory = None      # Directory containing chandler executable
notificationManager = None    # NotificationManager
repository = None             # The repository
mainView = None               # The main View
wxApplication = None          # The wxWindows application object
activeView = None             # The last view that was displayed
crypto = None                 # Cryptographic services

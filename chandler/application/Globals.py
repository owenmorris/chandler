__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
  Globals variables

  Initialized by Application, which must be created before they can be used.
Don't add to the globals without reviewing the addition. 
"""

__all__ = [ 'application',
            'association',
            'chandlerDirectory',
            'repository',
            'jabberClient',
            'wxMainFrame' ]


agentManager = None       # The wxApplication object
application = None        # The wxApplication object
association = {}          # A dictionary mapping persistent object ids
                          #    to non-persistent wxPython counterparts
chandlerDirectory = None  # Directory containing chandler executable
repository = None         # The repository
jabberClient = None       # State of jabber client including presence dictionary
wxMainFrame = None        # Active wxChandlerWindow

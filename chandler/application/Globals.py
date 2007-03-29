#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

"""
  Globals variables and options

  Importing this file initializes the command line options

  Initialized by Application, which must be created before they can be used.
  Don't add to the globals without reviewing the addition.
"""
import thread
from application.Utility import initDefaults


chandlerDirectory = None      # Directory containing chandler executable
wxApplication = None          # The application object. Use only to test to see if we have
                              # an application. Use wx.GetApp() to get the application object.
mailService = None            # Mail Service (IMAP, POP, SMTP)
options = initDefaults()      # Command line options
UI_Thread = thread.get_ident()# UI thread ID

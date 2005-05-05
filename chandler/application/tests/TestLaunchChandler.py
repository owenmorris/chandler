"""
Launch Chandler from the unit test world
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, traceback, unittest
import Chandler
import application.Globals as Globals
import application.Application as Application

"""
Overview:
    HardHat -> LaunchChandlerTest -> Chandler.main -> Chandler.realMain -> new wxApplication, wxApplication.mainLoop

Issues:
    * Failure when trying to create a wxApplication leaves running threads.  This is a bug.
        This can happen due to a syntax error during startup, like garbage at the bottom of Main.py.
    * Scripts are run during wxApplication.Idle time.  
        This is a bit of a problem because only one idle happens until the mouse moves.
        For now, we just run the whole script on the first idle.
    * Exceptions don't always make their way all the way out to the caller, my unit test:
        - errors that happen in response to a user event seem to be caught by the main loop.
        - in this case, Chandler will never Quit, so our unit test will hang.
    * The failure message isn't great.  It gives the last 5 frames, but not the error.
"""

class LaunchChandlerTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testLaunchChandler(self):
        """ Test Launching Chandler """
        # Set up the environment for non-catching
        os.environ['NOCATCH'] = '1'

        # Script to execute
        os.environ['STARTUPSCRIPT'] = "Quit"

        # Launch Chandler
        try:
            didLaunch = False
            Chandler.main()
            didLaunch = True
            message = "OK"
        # Catch exceptions that come all the way out, e.g. parcel.xml issues.
        except Exception, exception:
            type, value, stack = sys.exc_info()
            formattedBacktrace = "".join (traceback.format_exception (type, value, stack, 5))
            message = ("Chandler encountered an unexpected problem which caused this unit test to fail.\n" + \
                      "Here are the bottom 5 frames of the stack:\n%s") % formattedBacktrace
        self.assert_(didLaunch, message)

if __name__ == "__main__":
    unittest.main()

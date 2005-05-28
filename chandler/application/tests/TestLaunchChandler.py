"""
Launch Chandler from the unit test world
"""
__revision__  = "$Revision: 1.1 $"
__date__      = "$Date: 2005/05/05 05:43:43 $"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ParcelLoaderTestCase, os, sys, traceback, unittest
import Chandler
import application.Globals as Globals
import application.Application as Application
import application

""" Test Launching Chandler """

class LaunchChandlerTestCase(ParcelLoaderTestCase.ParcelLoaderTestCase):

    def testLaunchChandler(self):
        """ Test Launching Chandler """

        # Script to execute
        scriptToExecute = "Quit"

        # Set up the environment for non-catching and a fresh repository
        chandlerArgs = ['Chandler.py', '--nocatch', '--create']

        # Set up the script argument
        chandlerArgs.append('--script=%s' % scriptToExecute)

        """
        Use the scheme from Chandler.main() to locate the chandler directory, and 
            use it as the profile directory.
        """
        pathComponents = sys.modules['Chandler'].__file__.split(os.sep)
        assert len(pathComponents) > 2
        chandlerDirectory = os.sep.join(pathComponents[0:-1])
        profileDir = chandlerDirectory

        # Don't use the normal user's repo, redirect to the directory Chandler lives in
        chandlerArgs.append('--profileDir=%s' % profileDir)

        # modify the args, so Chandler will pick them up, not the Hardhat
        #   args used to invoke this unit test.
        sys.argv = chandlerArgs

        # Launch Chandler
        didLaunch = False
        message = "OK"
        try:
            Chandler.main()
            didLaunch = True

        # Catch exceptions that come all the way out, e.g. parcel.xml issues.
        except Exception, exception:
            type, value, stack = sys.exc_info()
            formattedBacktrace = "".join (traceback.format_exception (type, value, stack, 5))
            message = ("Chandler encountered an unexpected problem which caused this unit test to fail.\n" + \
                      "Here are the bottom 5 frames of the stack:\n%s") % formattedBacktrace

        # fail the test if we did not launch
        self.assert_(didLaunch, message)

        # @@@DLD - split off a timer task to kill chandler in case it never came back.

if __name__ == "__main__":
    unittest.main()

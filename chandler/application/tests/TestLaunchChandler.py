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

        # You must set this environment variable, or this test is a noop.
        if os.environ.get('CHANDLER_LAUNCH_TEST'):

            # Set up the environment for non-catching and a fresh repository
            chandlerArgs = ['Chandler.py', '--nocatch', '--create']
    
            # Set up the script argument
            chandlerArgs.append('--testScripts')
    
            # User's can specify the profile directory to use for the launch test
            profileDir = os.environ.get('CHANDLER_LAUNCH_TEST_PROFILEDIR')
            if not profileDir:

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
            Chandler.main()
    
            # @@@DLD - split off a timer task to kill chandler in case it never came back.

if __name__ == "__main__":
    unittest.main()

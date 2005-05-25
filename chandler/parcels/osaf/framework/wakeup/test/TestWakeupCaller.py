__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Unit test for message parsing """

import repository.tests.RepositoryTestCase as RepositoryTestCase
import osaf.framework.wakeup.WakeupCaller as WakeupCaller
import osaf.framework.wakeup.WakeupCallerParcel as WakeupCallerParcel
import osaf.framework.twisted.TwistedReactorManager as TwistedReactorManager
import application.Globals as Globals
import unittest as unittest
import time
import repository.schema.Types as Types

from datetime import datetime, timedelta

DATA = [None, 0, False] #UUID, Number of times called, UUID's Equal

class WakeupCallTest(WakeupCaller.WakeupCall):
    def receiveWakeupCall(self, wakeupCallItem):
        global DATA

        if DATA[1] == 0:
            DATA[2]  = wakeupCallItem.itsUUID == DATA[0]

        DATA[1] += 1

        if DATA[1] == 2:
            wakeupCallItem.enabled = False
            wakeupCallItem.itsView.commit()
            Globals.wakeupCaller.refresh()

class WakeupCallerTestCase(RepositoryTestCase.RepositoryTestCase):
    def testWakeupCall(self):
        """
            Unit test for C{WakeupCaller}. Performs the following operations:
                1. Create a C{WakeupCall} item with repeat set to True and the delay set to five
                   seconds
                2. Commit the C{WakeupCall} to the Repository and call refresh on the
                   C{WakeupCaller}
                3. Have the C{WakeupCallTest} be called 2 times then set the enabled flag
                   to False, commit, and refresh the C{WakeupCaller}
                4. Delete the C{WakeupCall} in the repository
                5. Perform the following tests

            Tests:
                1. UUID of C{WakeupCall} matches UUID of C{WakeupCall} passed to C{WakeupCallTest}
                2. The C{WakeupCallTest} receiveWakeupCall method was called twice
        """

        global DATA
        wakeupCall = WakeupCallerParcel.WakeupCall(view=self.rep.view)

        wakeupCall.wakeupCallClass = WakeupCallTest
        wakeupCall.delay  = timedelta(seconds=5)
        wakeupCall.repeat = True

        DATA[0] = wakeupCall.itsUUID
        
        self.rep.view.commit()
        Globals.wakeupCaller.refresh()

        #Wait for the WakeupCaller to call the WakeupCallTest 2 times
        time.sleep(60)

        wakeupCall.delete()
        self.rep.view.commit()

        self.assertEquals(DATA[1], 2)
        self.assertEquals(DATA[2], True)

    def setUp(self):
        super(WakeupCallerTestCase, self).setUp()
        self.loadParcel("http://osafoundation.org/parcels/osaf/contentmodel")
        self.loadParcel("http://osafoundation.org/parcels/osaf/framework/wakeup")

        self.rep.view.commit()

        Globals.twistedReactorManager = TwistedReactorManager.TwistedReactorManager()
        Globals.twistedReactorManager.startReactor()

        Globals.wakeupCaller = WakeupCaller.WakeupCaller(self.rep)
        Globals.wakeupCaller.startup()

    def tearDown(self):
        Globals.wakeupCaller.shutdown()
        Globals.twistedReactorManager.stopReactor()
        Globals.wakeupCaller = None
        Globals.twistedReactorManager = None

if __name__ == "__main__":
   unittest.main()

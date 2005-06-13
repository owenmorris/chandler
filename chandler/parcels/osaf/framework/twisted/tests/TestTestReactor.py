from osaf.framework.twisted import testreactor
from twisted.internet import reactor, defer
import unittest, time

class TestTestReactor(testreactor.ReactorTestCase):
    """Test the actual testing functionality of testreactor"""

    def testSimulatedTimeFunctions(self):
        now = reactor.getTime()
        delay = 15
        reactor.sleep(delay)
        self.assertEqual(reactor.getTime(), now+delay)

        reactor.setTime(now)  # put the clock back
        self.assertEqual(reactor.getTime(), now)

    def testWaitFor(self):
        cb = reactor.callLater(5, reactor.crash)
        self.assertRaises(
            testreactor.EarlyExit,
            lambda: reactor.waitFor(10, early_ok=False)
        )
        self.failIf(cb.active())    # The callback should've fired

        # The waitFor() does its scheduling *after* the callLater,
        # so its callback should fire second, assuming that the
        # reactor uses a stable sorting algorithm to schedule callbacks
        # Thus, even though the timeout is scheduled for the same moment
        # of simulated time, the following should not raise an error.
        cb = reactor.callLater(5, reactor.crash)
        reactor.waitFor(5, early_ok=False)
        self.failIf(cb.active())    # The callback should've fired

        # Finally, test some simple cases...
        cb = reactor.callLater(3, reactor.crash)
        reactor.waitFor(2)
        self.failUnless(cb.active())    # The callback shouldn't have fired yet

        reactor.waitFor(1)
        self.failIf(cb.active())    # Now it should've fired

    def testWaitUntil(self):
        # Wait for a deferred that doesn't fire within the timeout
        d = defer.Deferred()
        self.assertRaises(
            testreactor.TimeoutError,
            lambda: reactor.waitUntil(d, 1440)  # wait "all day" and time out
        )

        # Now fire it in 5 seconds and get what we want
        reactor.callLater(5, d.callback, "Ping!")
        self.assertEqual( reactor.waitUntil(d, 5), "Ping!")

        # Fired before loop starts -> immediate return
        d = defer.Deferred()
        d.callback("Pong")
        self.assertEqual( reactor.waitUntil(d, 0), "Pong")

        # Errors from the deferred should be communicated back to caller
        class my_error(Exception): pass

        d = defer.Deferred()
        def throw_me():
            try:
                raise my_error
            except:
                d.errback()

        reactor.callLater(3,throw_me)
        self.assertRaises(my_error, lambda: reactor.waitUntil(d,5))


    def testCleanupAfterEarlyExit(self):
        d = defer.Deferred()
        reactor.callLater(1,reactor.crash)  # exit early
        self.assertRaises(
            testreactor.EarlyExit,
            lambda:reactor.waitUntil(d, 5)
        )
        reactor.callLater(10, d.callback, "Done")
        self.assertEqual(reactor.waitUntil(d, 10), "Done")

    def testReactorResetsScheduledCalls(self):
        reactor.callLater(5, reactor.crash)
        reactor.waitFor(3)
        reactor.start()     # reset reactor completely
        reactor.waitFor(10, False)  # this should fail if callback is active

    def testModeChanges_1(self):
        reactor.useRealTime()
        reactor.useRealTime()
        reactor.useRealTime()
        self.assertRaises(AssertionError, reactor.useSimulatedTime)
        self.failIf(self.isSimulated())

    def testModeChanges_2(self):
        reactor.useSimulatedTime()
        reactor.useSimulatedTime()
        reactor.useSimulatedTime()
        self.assertRaises(AssertionError, reactor.useRealTime)
        self.failUnless(self.isSimulated())

    def isSimulated(self):
        """Reactor time is simulated if the clock doesn't go forward"""
        now = reactor.getTime()
        time.sleep(0.001)               # Ensure "real time" advances
        return reactor.getTime()==now   # If reactor doesn't, it's simulated

    def testRealTimeIsReal(self):
        reactor.useRealTime()
        self.failIf(self.isSimulated())

        # shouldn't let us set the time, either
        self.assertRaises(AssertionError, lambda: reactor.setTime(0))

    def testSimulatedTimeIsSimulated(self):
        reactor.useSimulatedTime()
        self.failUnless(self.isSimulated())





class TestReactorTestCase(unittest.TestCase):
    """Test the ReactorTestCase class, and the install/uninstall methods"""

    def setUp(self):
        class Mixin(unittest.TestCase):
            """This mixin is a placeholder used to verify that ReactorTestCase
            setUp/tearDown call their superclass setUp/tearDown.  This is
            important if, for example, you mix a ReactorTestCase with some
            other test case base class.
            """
            gotSetUp = gotTearDown = False

            def setUp(self):
                self.gotSetUp = True

            def tearDown(self):
                self.gotTearDown = True

        class TestClass(testreactor.ReactorTestCase, Mixin):
            def testNothing(self):
                """This is just to have a test to call"""

        self.testInstance = TestClass("testNothing")

    install_ran = False
    uninstall_ran = False

    def testSetupInstalls(self):
        old = testreactor.install, testreactor.uninstall
        def install():
            self.install_ran = True
        def uninstall():
            self.uninstall_ran = True

        try:
            testreactor.install, testreactor.uninstall = install, uninstall
            self.testInstance.setUp()
            self.testInstance.tearDown()
        finally:
            testreactor.install, testreactor.uninstall = old

        self.failUnless(self.install_ran)
        self.failUnless(self.uninstall_ran)

    def testSetupSuperclass(self):
        self.testInstance.setUp()
        self.failUnless(self.testInstance.gotSetUp)

    def testTearDownSuperclass(self):
        self.testInstance.tearDown()
        self.failUnless(self.testInstance.gotTearDown)



if __name__ == '__main__':
    unittest.main()



























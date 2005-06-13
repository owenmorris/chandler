"""Support for writing Twisted unit tests"""

from twisted.internet import reactor, selectreactor, base, task
from twisted.internet.selectreactor import _select as realselect
from twisted.python.runtime import seconds as realtime
from twisted.python import failure
from time import sleep as realsleep
import unittest

__all__ = [
    "install", "uninstall", "ReactorTestCase", "TimeoutError", "EarlyExit"
]


class TimeoutError(AssertionError):
    """A requested timeout expired

    This is a subclass of AssertionError so that unittest will treat tests
    raising it as "Failed" rather than as being in "Error".  So, you don't
    need to trap and reraise this error; just let it pass through.
    """

class EarlyExit(AssertionError):
    """The run loop was exited sooner than expected (e.g. before a result)
    
    This is a subclass of AssertionError so that unittest will treat tests
    raising it as "Failed" rather than as being in "Error".  So, you don't
    need to trap and reraise this error; just let it pass through.
    """


# Note - the class below includes 'object' in its bases so that __mro__
# will be sane for super() use when mixed with other TestCase derivatives
#
class ReactorTestCase(unittest.TestCase, object):
    """Test case mixin that ensures the test reactor is ready for use

    Note that if you include other TestCase-derived base classes in your
    subclass' bases, you should include them *after* this class, to ensure
    that this class' setUp/tearDown methods get called.  (It will then call
    the remaining classes' setUp and tearDown methods using super().)
    """

    def setUp(self):
        super(ReactorTestCase,self).setUp()
        install()

    def tearDown(self):
        uninstall()
        super(ReactorTestCase,self).tearDown()


class TestReactor(selectreactor.SelectReactor):
    """Add test-specific features to the Twisted default reactor"""

    def start(self):
        """Reset the reactor completely

        You don't need to use this if you use ReactorTestCase, which wraps your
        tests in fresh restarts.
        """
        self.__dict__.clear()
        self.__init__()
        self._simulated_time = realtime()
        self._use_realtime = None
        

    def waitFor(self, seconds, early_ok=True):
        """Run the event loop for `seconds` of simulated time

        If `early_ok` is set to False, this raises EarlyExit if the runloop
        exits before the time expires.
        """
        finish = self.callLater(seconds, self.crash)
        self.running = 1
        self.mainLoop()
        if finish.active():
            finish.cancel()
            if not early_ok:
                raise EarlyExit("Reactor exited before %s seconds" % seconds)

    def waitUntil(self, deferred, timeout):
        """Return a result or error from `deferred`

        `timeout` is a timeout value in seconds of simulated time.  If the
        timeout elapses without a result or error from the deferred,
        TimeoutError is raised.  This can also raise EarlyExit if the runloop
        is exited without the deferred having fired.
        """
        finish = self.callLater(timeout, self.crash)
        result = []

        def callback(value):
            if finish.active():
                # Only stop the reactor if the original call
                # is still active
                finish.cancel()
                self.crash()
                result.append(value)
                if isinstance(value,failure.Failure):
                    value = None    # don't pass on an exception
            # always return the value, so that any chained callbacks work
            return value

        deferred.addCallbacks(callback, callback) # call it either way

        if not result:  # don't infinite loop if the deferred has already fired
            self.running = 1
            self.mainLoop()

        if result:
            result, = result
            if isinstance(result,failure.Failure):
                result.raiseException()
            return result

        if finish.active():
            finish.cancel()
            raise EarlyExit("Reactor exited before a result was produced")
        else:
            raise TimeoutError("%s simulated seconds elapsed" % timeout)
        
    def getTime(self):
        """Get the current simulated (or real) time"""
        if self._use_realtime:
            return realtime()
        self._use_realtime = False  # once we've read it, disallow changing it
        return self._simulated_time

    def setTime(self,seconds):
        """Set the current simulated time"""
        if self._use_realtime:
            raise AssertionError("Can't set time when using real time")
        self._simulated_time = seconds

    def sleep(self,seconds):
        """Advance the simulated clock, or sleep for the number of seconds"""
        if self._use_realtime:
            realsleep(seconds)
        else:
            self.setTime(self.getTime()+seconds)

    def select(self,r,w,e,timeout=None):
        """Pretend the select() time elapses, then select for 0 seconds"""
        if not self._use_realtime:
            if timeout is not None:
                self.sleep(timeout)
            timeout = 0
        return realselect(r,w,e,timeout)


    def _setMode(self,mode):
        if self._use_realtime is not None and self._use_realtime<>mode:
            raise AssertionError(
                "Cannot change clock mode without restarting reactor"
            )
        self._use_realtime = mode

    def useRealTime(self):
        """Use wall-clock time for the current test"""
        self._setMode(True)

    def useSimulatedTime(self):
        """Use simulated time for the current test (default)"""
        self._setMode(False)


def install():
    """Install and reset the test reactor"""
    if not isinstance(reactor,TestReactor):
        assert reactor.__class__ is selectreactor.SelectReactor, (
            "testreactor can only be installed over the default reactor"
        )
        reactor.__class__ = TestReactor

    reactor.start()

    # If Twisted defined these as methods on reactors, we wouldn't
    # need to monkeypatch their globals like this.  :(
    base.seconds = reactor.getTime
    task.seconds = reactor.getTime
    selectreactor.sleep = reactor.sleep
    selectreactor._select = reactor.select


def uninstall():
    """Shut down and uninstall the test reactor"""
    try:
        if reactor.running:
            reactor.stop()
    finally:
        if isinstance(reactor,TestReactor):
            reactor.__class__ = selectreactor.SelectReactor
        
        # Use real time
        base.seconds = realtime
        task.seconds = realtime
        selectreactor.sleep = realsleep
        selectreactor._select = realselect


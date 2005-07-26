"""Extension Point for Application Startup"""

from application import schema
from repository.persistence.Repository import RepositoryThread
import threading

__all__ = [
    'Startup', 'run_startup', 'Thread', 'run_in_thread',
    'get_reactor_thread', 'run_reactor', 'stop_reactor',
]


# --------
# Startups
# --------

def run_startup(repositoryView):
    """Run all active startup items in `repositoryView`"""
    started = set()
    attempted = set()
    for item in Startup.iterItems(repositoryView):
        item._start(attempted, started)


class Startup(schema.Item):
    """Subclass this & create parcel.xml instances for startup notifications"""

    invoke = schema.One(schema.String,
        doc="Full name of a class or function to import and run at startup"
    )

    active = schema.One(schema.Boolean,
        doc="Set to False to disable invocation of this item at startup",
        initialValue=True,
    )

    requires = schema.Sequence("Startup",
        doc="Startups that must run before this one",
        initialValue=[]
    )

    requiredBy = schema.Sequence(inverse=requires)

    def onStart(self):
        """Override this method in a subclass to receive the notification

        Note: you should *not* create or modify items in this method or code
        called from this method.  If you want to do that, you probably don't
        want to be using a Startup item.

        Also note that you should not call invoke this method via super()
        unless you want the default behavior (i.e., importing and running the
        ``invoke`` attribute) to occur.
        """
        schema.importString(self.invoke)(self)

    def _start(self, attempted, started):
        """Handle inter-startup ordering and invoke onStart()"""
        if self in started:
            return True
        elif not self.active or self in attempted:
            return False

        attempted.add(self)   # prevent multiple attempts to start this item
        canStart = True
        for item in self.requires:
            canStart = canStart and item._start(attempted, started)
        
        if canStart:
            self.onStart()
            started.add(self)
            return True

        return False


# -------
# Threads
# -------

class Thread(Startup):
    """A Startup that runs its `invoke` target in a new thread"""

    def onStart(self):
        run_in_thread(schema.importString(self.invoke), self).start()


class run_in_thread(RepositoryThread):
    """Call `code(item)` in a new thread with its own repository view"""

    def __init__(self, code, item):
        self.view = item.itsView
        self.uuid = item.itsUUID
        self.code = code
        repo = self.view.repository
        if repo is not None:
            self.view = repo.createView()
        super(run_in_thread, self).__init__(name=str(item.itsPath))
        self.setDaemon(True)    # main thread can exit even if this one hasn't

    def run(self):
        if self.view.repository is not None:
            self.view.setCurrentView()
        self.code(self.view.findUUID(self.uuid))



# ------------------
# Reactor Management
# ------------------

_reactor_thread = None


def get_reactor_thread():
    """Return the threading.thread running the Twisted reactor, or None"""
    return _reactor_thread
    

def run_reactor(in_thread=True):
    """Safely run the Twisted reactor"""

    global _reactor_thread

    from twisted.python import threadable
    threadable.init()
    from twisted.internet import reactor

    if not in_thread:
        if reactor.running:
            raise AssertionError("Reactor is already running")
        # enable repeated reactor runs
        for evt in reactor.crash, reactor.disconnectAll:
            reactor.addSystemEventTrigger('during', 'shutdown', evt)
        reactor.run(0)
        return

    import sys

    if _reactor_thread is None:
        if threading.currentThread().getName() != "MainThread":
            raise AssertionError(
                "can't start reactor thread except from the main thread"
            )
        limbo = [1]
        reactor.addSystemEventTrigger('before', 'startup', limbo.pop)
        _reactor_thread = RepositoryThread(
            name="reactor", target=run_reactor, args=(False,)
        )
        _reactor_thread.setDaemon(True) # let main thread exit even if running
        _reactor_thread.start()

        while limbo and _reactor_thread.isAlive():
            pass   # wait for reactor to start or thread to die (e.g. w/error)

        if not _reactor_thread.isAlive():
            _reactor_thread = None

    
def stop_reactor():
    """Stop the Twisted reactor and wait for its thread to exit"""
    
    global _reactor_thread
    from twisted.internet import reactor

    if reactor.running:
        reactor.callFromThread(reactor.stop)

    if _reactor_thread is not None:
        if _reactor_thread.isAlive():
            _reactor_thread.join()
        _reactor_thread = None



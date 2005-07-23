"""Extension Point for Application Startup"""

from application import schema
from repository.persistence.Repository import RepositoryThread

__all__ = ['Startup', 'Thread', 'run_in_thread', 'run_startup']


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




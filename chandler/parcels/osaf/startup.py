"""Extension Point for Application Startup"""

from application import schema

__all__ = ['Startup', 'run_startup']


def run_startup(repositoryView):
    """Run all active startup items in `repositoryView`"""
    started = set()
    attempted = set()
    for item in Startup.iterItems(repositoryView):
        item._start(attempted, started)


class Startup(schema.Item):
    """Subclass this & create parcel.xml instances for startup notifications"""

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
        """

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


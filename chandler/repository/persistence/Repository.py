
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import logging, threading, PyLucene

from chandlerdb.util.uuid import UUID
from repository.item.Item import Item
from repository.persistence.RepositoryView import RepositoryView
from repository.persistence.RepositoryView import OnDemandRepositoryView
from repository.persistence.RepositoryError import RepositoryError


class Repository(object):
    """
    An abstract repository for items.

    The repository has direct access to its roots by name and to all its
    items by UUID. It can be used as an iterator over all its roots.
    """

    def __init__(self, dbHome):
        """
        Instantiate a repository.

        @param dbHome: the filesystem directory that serves as the home
        location for the repository's files
        @type dbHome: a string
        """

        super(Repository, self).__init__()

        self.dbHome = dbHome
        self._status = 0
        self._threaded = threading.local()
        self._notifications = []
        self._openViews = []

    def __repr__(self):

        return "<%s>" %(type(self).__name__)

    def create(self, **kwds):
        """
        Create a new repository in C{self.dbHome}. Some implementations may
        remove files for existing repositories in the same location.

        A number of keywords can be passed to this method. Their support
        depends on the actual implementation chosen for the persistence
        layer.
        
        @param ramdb: a keyword argument that causes the repository to be
        created in memory instead of in the underlying file system.
        C{False} by default, supported by C{DBRepository} only.
        @type ramdb: boolean
        """

        self._init(**kwds)
        
    def open(self, **kwds):
        """
        Open a repository in C{self.dbHome}.

        A number of keywords can be passed to this method. Their support
        depends on the actual implementation chosen for the persistence
        layer.
        
        @param create: a keyword argument that causes the repository to be
        created if no repository exists in C{self.dbHome}. C{False}, by
        default.
        @type create: boolean
        @param ramdb: a keyword argument that causes the repository to be
        created in memory instead of using the underlying file system.
        C{False} by default, supported by C{DBRepository} only.
        @type ramdb: boolean
        @param recover: a keyword argument that causes the repository to be
        opened with recovery. C{False} by default, supported by
        C{DBRepository} only.
        @type recover: boolean
        @param exclusive: a keyword argument that causes the repository to be
        opened with exclusive access, preventing other processes from
        opening it until this process closes it. C{False} by default,
        supported by C{DBRepository} only.
        @type exclusive: boolean
        """

        self._init(**kwds)

    def delete(self):
        """
        Delete a repository.

        Files for the repository in C{self.dbHome} are removed.
        """
        
        raise NotImplementedError, "%s.delete" %(type(self))

    def _init(self, **kwds):

        self._status = 0
        self.logger = logging.getLogger('repository')

        if kwds.get('debug', False):
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        if kwds.get('stderr', False) or not self.logger.root.handlers:
            if not self.logger.handlers:
                self.logger.addHandler(logging.StreamHandler())

        if kwds.get('refcounted', False):
            self._status |= Repository.REFCOUNTED
            
    def _isRepository(self):

        return True

    def _isView(self):

        return False

    def _isItem(self):

        return False
    
    def close(self):
        """
        Close the repository.

        The repository's underlying persistence implementation is closed.
        """
        
        pass

    def prune(self, size):
        """
        Prune the current repository view.

        See L{RepositoryView.prune
        <repository.persistence.RepositoryView.RepositoryView.prune>}
        for more details.
        """
        
        self.view.prune(size)

    def closeView(self, purge=False):
        """
        Close the current repository view.

        See L{RepositoryView.close
        <repository.persistence.RepositoryView.RepositoryView.close>}
        for more details.
        """

        self.view.closeView()

    def openView(self):
        """
        Open the current repository view.

        See L{RepositoryView.open
        <repository.persistence.RepositoryView.RepositoryView.open>}
        for more details.
        """

        self.view.openView()

    def createView(self, name=None, version=None):
        """
        Create a repository view.

        The repository view is created open. See L{RepositoryView
        <repository.persistence.RepositoryView.RepositoryView>}
        for more details.

        @param name: the optional name of the view. By default, the name of
        the repository view is set to the name of the thread creating it
        which assumed to the threading for which it is intended.
        @type name: a string
        """

        return RepositoryView(self, name, version)

    def commit(self, mergeFn=None):
        """
        Commit changes in the current repository view.

        See L{RepositoryView.commit
        <repository.persistence.RepositoryView.RepositoryView.commit>}
        for more details.
        """
        
        if not self.isOpen():
            raise RepositoryError, "Repository is not open"

        self.view.commit()

    def refresh(self, mergeFn=None):
        """
        Refresh the current repository view to the changes made in other views.

        See L{RepositoryView.refresh
        <repository.persistence.RepositoryView.RepositoryView.refresh>}
        for more details.
        """
        
        if not self.isOpen():
            raise RepositoryError, "Repository is not open"

        self.view.refresh()

    def cancel(self):
        """
        Cancel changes in the current repository view.

        See L{RepositoryView.cancel
        <repository.persistence.RepositoryView.RepositoryView.cancel>}
        for more details.
        """

        if not self.isOpen():
            raise RepositoryError, "Repository is not open"

        self.view.cancel()

    def getCurrentView(self, create=True):
        """
        Get the current repository view.

        Each thread may have a current repository view. If the current
        thread has no repository view, this method creates and sets one for
        it if C{create} is C{True}, the default.

        @param create: create a view if none exists for the current
        thread, C{True} by default
        @type create: boolean
        """

        try:
            return self._threaded.view

        except AttributeError:
            if create:
                view = self.createView()
                self.setCurrentView(view)

                return view

        return None

    def setCurrentView(self, view):
        """
        Set the current view for the current thread.

        @param view: a repository view
        @type view: a L{RepositoryView<repository.persistence.RepositoryView.RepositoryView>} instance
        @return: the view that was current for the thread before this call.
        """

        if view is not None and view.repository is not self:
            raise RepositoryError, 'Repository does not own view: %s' %(view)

        previous = self.getCurrentView(False)
        self._threaded.view = view

        return previous

    def getOpenViews(self):

        return self._openViews

    def __iter__(self):
        """
        (deprecated) Use L{iterRoots} instead.
        """

        raise DeprecationWarning, 'Use Repository.iterRoots() instead'

    def iterRoots(self, load=True):
        """
        Iterate over the roots of this repository using the current view.
        """

        return self.view.iterRoots(load)

    def isOpen(self):
        """
        Tell whether the repository is open.

        @return: C{True} or C{False}
        """

        return (self._status & Repository.OPEN) != 0

    def isRefCounted(self):

        return (self._status & Repository.REFCOUNTED) != 0

    def hasRoot(self, name, load=True):
        """
        Search the current view for a root.

        See L{RepositoryView.hasRoot
        <repository.persistence.RepositoryView.RepositoryView.hasRoot>}
        for more details.
        """

        return self.view.hasRoot(name, load)

    def getRoot(self, name, load=True):
        """
        Get a root by a given name.

        See L{RepositoryView.getRoot
        <repository.persistence.RepositoryView.RepositoryView.getRoot>}
        for more details.
        """

        return self.view.getRoot(name, load)

    def __getitem__(self, key):

        return self.view.__getitem__(key)

    def walk(self, path, callable, _index=0, **kwds):
        """
        Walk a path in the current view and invoke a callable along the way.

        See L{Item.walk<repository.item.Item.Item.walk>} for more details.
        """

        return self.view.walk(path, callable, _index, **kwds)

    def find(self, spec, load=True):
        """
        Find an item.

        See L{Item.find<repository.item.Item.Item.find>} for more details.
        """

        return self.view.find(spec, load)

    def findPath(self, path, load=True):
        """
        Find an item by path in the current view.

        See L{Item.findPath<repository.item.Item.Item.findPath>} for more
        details.
        """

        return self.view.findPath(path, load)

    def findUUID(self, uuid, load=True):
        """
        Find an item by UUID in the current view.

        See L{Item.findUUID<repository.item.Item.Item.findUUID>} for more
        details.
        """

        return self.view.findUUID(uuid, load)

    def queryItems(self, kind=None, attribute=None, load=True):
        """
        Query items in the current view.

        See L{RepositoryView.queryItems
        <repository.persistence.RepositoryView.RepositoryView.queryItems>}
        for more details.
        """

        return self.view.queryItems(query, load)

    def searchItems(self, query, load=True):
        """
        Search items in the current view using a lucene full text query.

        See L{RepositoryView.searchItems
        <repository.persistence.RepositoryView.RepositoryView.searchItems>}
        for more details.
        """

        return self.view.searchItems(query, load)

    def getACL(self, uuid, name):
        """
        Get an ACL from the repository using the current view.

        See L{RepositoryView.getACL
        <repository.persistence.RepositoryView.RepositoryView.getACL>}
        for more details.
        """

        return self.view.getACL(uuid, name)

    def loadPack(self, path, parent=None):
        """
        Load a repository pack into the current view.

        See L{RepositoryView.loadPack
        <repository.persistence.RepositoryView.RepositoryView.loadPack>}
        for more details.
        """

        self.view.loadPack(path, parent)

    def dir(self, item=None, path=None):
        """
        Print all item paths in the repository, a debugging feature.

        See L{RepositoryView.dir
        <repository.persistence.RepositoryView.RepositoryView.dir>}
        for more details.
        """

        self.view.dir(item, path)

    def check(self):
        """
        Runs repository consistency checks on the current view.

        See L{RepositoryView.check
        <repository.persistence.RepositoryView.RepositoryView.check>}
        for more details.
        """
        
        return self.view.check()

    def addNotificationCallback(self, fn):
        """
        Add a callback to receive repository notifications.

        After a view commits changes successfully, it sends out a number of
        notifications to the callbacks registered through this method.

        The callback needs to be able to accept the following arguments:

            - a an array of tuples (UUID, reason, kwds)
              - UUID, representing an item
              - a string, representing the reason
              - kwds, an arbitrary C{**kwds} dictionary containing more
                notification-specific values.
            - a string, one of C{ItemChanged}, C{CollectionChanged}, or
              C{History} 

        @param fn: the callback to add
        @type fn: a python callable
        """

        self._notifications.append(fn)

    def removeNotificationCallback(self, fn):
        """
        Remove a callback to receive repository notifications.

        @param fn: the callback to remove
        @type fn: a python callable
        """

        try:
            return self._notifications.pop(self._notifications.index(fn))
        except ValueError:
            return None

    def mapChanges(self, callable, freshOnly=False):

        self.view.mapChanges(callable, freshOnly)

    def mapHistory(self, callable, fromVersion=0, toVersion=0):

        self.view.mapHistory(callable, fromVersion, toVersion)

    def isDebug(self):

        return self.logger.getEffectiveLevel() <= logging.DEBUG
        
    def setDebug(self, debug):

        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    itsUUID = UUID('3631147e-e58d-11d7-d3c2-000393db837c')

    OPEN       = 0x0001
    REFCOUNTED = 0x0002
    RAMDB      = 0x0004

    view = property(getCurrentView, setCurrentView)
    views = property(getOpenViews)
    repository = property(lambda self: self)
    debug = property(isDebug, setDebug)


class OnDemandRepository(Repository):
    """
    An abstract repository for on-demand loaded items.
    """

    def createView(self, name=None, version=None):

        return OnDemandRepositoryView(self, name, version)


class Store(object):

    def __init__(self, repository):

        super(Store, self).__init__()
        self.repository = repository

    def open(self, create=False):
        raise NotImplementedError, "%s.open" %(type(self))

    def close(self):
        raise NotImplementedError, "%s.close" %(type(self))

    def getVersion(self):
        raise NotImplementedError, "%s.getVersion" %(type(self))

    def loadItem(self, version, uuid):
        raise NotImplementedError, "%s.loadItem" %(type(self))
    
    def serveItem(self, version, uuid, cloudAlias):
        raise NotImplementedError, "%s.serveItem" %(type(self))
    
    def serveChild(self, version, uuid, name, cloudAlias):
        raise NotImplementedError, "%s.serveChild" %(type(self))

    def loadRef(self, version, uItem, uuid, key):
        raise NotImplementedError, "%s.loadRef" %(type(self))

    def loadRefs(self, version, uItem, uuid, firstKey):
        raise NotImplementedError, "%s.loadRefs" %(type(self))

    def loadACL(self, version, uuid, name):
        raise NotImplementedError, "%s.loadACL" %(type(self))

    def queryItems(self, version, kind=None, attribute=None):
        raise NotImplementedError, "%s.queryItems" %(type(self))
    
    def searchItems(self, version, query):
        raise NotImplementedError, "%s.searchItems" %(type(self))
    
    def getItemVersion(self, version, uuid):
        raise NotImplementedError, "%s.getItemVersion" %(type(self))

    def attachView(self, view):
        pass

    def detachView(self, view):
        pass


class RepositoryNotifications(dict):

    def changed(self, uuid, reason, **kwds):

        self[uuid] = (reason, kwds)

    def history(self, uuid, reason, **kwds):

        self[uuid] = (reason, kwds)
    
    def dispatchHistory(self, view):

        callbacks = view.repository._notifications
        if callbacks:
            changes = []
            for uuid, (reason, kwds) in self.iteritems():
                changes.append( (uuid, reason, kwds) )
            for callback in callbacks:
                callback(view, changes, 'History')

        self.clear()


class RepositoryThread(PyLucene.PythonThread):
    pass

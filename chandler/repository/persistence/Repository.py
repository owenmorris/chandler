#   Copyright (c) 2004-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import sys, logging, threading, PyLucene

from chandlerdb.util.c import UUID
from chandlerdb.persistence.c import CRepository
from repository.item.Item import Item
from repository.persistence.RepositoryView import RepositoryView
from repository.persistence.RepositoryView import OnDemandRepositoryView
from repository.persistence.RepositoryError import RepositoryError


class Repository(CRepository):
    """
    An abstract repository for items.
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
        self._threaded = threading.local()
        self._openViews = []
        self._indexer = None

    def __repr__(self):

        return "<%s>" %(type(self).__name__)

    def create(self, **kwds):
        """
        Create a new repository in C{self.dbHome}. Some implementations may
        remove files for existing repositories in the same location.

        A number of keywords can be passed to this method. Their support
        depends on the actual implementation chosen for the persistence
        layer.
        """

        self._init(**kwds)
        
    def open(self, **kwds):
        """
        Open a repository in C{self.dbHome}.

        A number of keywords can be passed to this method. Their support
        depends on the actual implementation chosen for the persistence
        layer::
        
            create:    a keyword argument that causes the repository to be
                       created if no repository exists in C{self.dbHome}.
                       C{False}, by default.
            ramdb:     a keyword argument that causes the repository to be
                       created in memory instead of using the underlying
                       file system.
                       C{False} by default, supported by C{DBRepository} only.
            recover:   a keyword argument that causes the repository to be
                       opened with recovery.
                       C{False} by default, supported by C{DBRepository} only.
            exclusive: a keyword argument that causes the repository to be
                       opened with exclusive access, preventing other processes
                       from opening it until this process closes it.
                       C{False} by default, supported by C{DBRepository} only.
        """

        self._init(**kwds)

    def delete(self):
        """
        Delete a repository.

        Files for the repository in C{self.dbHome} are removed.
        """
        
        raise NotImplementedError, "%s.delete" %(type(self))

    def backup(self, dbHome=None):

        raise NotImplementedError, "%s.backup" %(type(self))

    def _init(self, **kwds):

        self._status = Repository.CLOSED
        self.logger = logging.getLogger('repository')

        def addHandler():
            for handler in self.logger.handlers:
                if (isinstance(handler, logging.StreamHandler) and
                    handler.stream is sys.stderr):
                    return
            self.logger.addHandler(logging.StreamHandler())

        if not kwds.get('logged', False):
            self.logger.setLevel(logging.INFO)
            addHandler()
        elif kwds.get('stderr', False):
            addHandler()

        if kwds.get('refcounted', False):
            self._status |= Repository.REFCOUNTED

        if kwds.get('verify', False):
            self._status |= Repository.VERIFY

    def close(self):
        """
        Close the repository.

        The repository's underlying persistence implementation is closed.
        """
        
        pass

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

    def isNew(self):

        return self.store.getVersion() == 0

    def setDebug(self, debug):

        if debug:
            self.logger.setLevel(logging.DEBUG)
            self._status |= Repository.DEBUG
        else:
            self.logger.setLevel(logging.INFO)
            self._status &= ~Repository.DEBUG

    itsUUID = RepositoryView.itsUUID
    view = property(getCurrentView, setCurrentView)
    views = property(getOpenViews)


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

    def loadItem(self, view, version, uuid):
        raise NotImplementedError, "%s.loadItem" %(type(self))
    
    def loadValue(self, view, version, uuid, name):
        raise NotImplementedError, "%s.loadValue" %(type(self))
    
    def loadRef(self, view, version, uItem, uuid, key):
        raise NotImplementedError, "%s.loadRef" %(type(self))

    def loadRefs(self, view, version, uItem, uuid, firstKey):
        raise NotImplementedError, "%s.loadRefs" %(type(self))

    def loadACL(self, view, version, uuid, name):
        raise NotImplementedError, "%s.loadACL" %(type(self))

    def queryItems(self, view, version, kind=None, attribute=None):
        raise NotImplementedError, "%s.queryItems" %(type(self))
    
    def queryItemKeys(self, view, version, kind=None, attribute=None):
        raise NotImplementedError, "%s.queryItemKeys" %(type(self))

    def kindForKey(self, view, version, uuid):
        raise NotImplementedError, "%s.kindForKey" %(type(self))
    
    def searchItems(self, view, version, query, attribute=None):
        raise NotImplementedError, "%s.searchItems" %(type(self))
    
    def getItemVersion(self, view, version, uuid):
        raise NotImplementedError, "%s.getItemVersion" %(type(self))

    def attachView(self, view):
        pass

    def detachView(self, view):
        pass


class RepositoryThread(PyLucene.PythonThread):
    pass

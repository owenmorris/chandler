
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import logging

from repository.persistence.RepositoryError \
    import RepositoryError, VersionConflictError
from repository.persistence.Repository import RepositoryThread
from chandlerdb.util.uuid import UUID


class AbstractRepositoryViewManager(object):

    def __init__(self, repository, viewName=None, version=None):
        """
        Base Class for View Context Management.

        @param repository: a Repository instance
        @type repository: C{Repository}
        @param viewName: The name to assign as the key for the view if None
                         an abitrary name will be assigned
        @type name: a string
        @return: C{None}
        """

        if repository is None:
            raise RepositoryError, "Repository Instance is None"

        if viewName is None:
            viewName = str(UUID())

        self.repository = repository
        self.view = self.repository.createView(viewName, version)
        self.prevView = None
        self.callChain = False
        self.log = self._getLog()

    def _getLog(self):
        """
        This method is called by the __init__ method to retrieve a C{logging.Logger} for
        logging.

        This method can be sub-classed to return a custom logger by the child.

        @return: C{logging.Logger}
        """

        log = logging.getLogger(__name__)
        return log

    def setViewCurrent(self):
        """
        This method changes the current C{RepositoryView} to be the C{RepositoryView} associated with the 
        C{AbstractRepositoryViewManger} instance.

        It saves the previous C{RepositoryView}. Calling C{AbstractRepositoryViewManager.restorePreviousView} will
        set the previous C{RepositoryView} as the current C{RepositoryView}.

        @return: C{None}
        """

        assert self.callChain is False, "setViewCurrent called again before a restorePreviousView"

        assert self.prevView is None, "Nested prevView investigate"
        self.prevView = self.getCurrentView()
        self.repository.setCurrentView(self.view)

        self.callChain = True


    def restorePreviousView(self):
        """
        This method will restore the C{RepositoryView} that was current before 
        C{AbstractRepositoryViewManager.setViewCurrent} when called.

        The C{AbstractRepositoryViewManager.setViewCurrent} method must be called before this method.

        @return: C{None}
        """

        if self.callChain is not True:
            raise RepositoryError, "restorePreviousView called before setViewCurrent"

        if self.prevView is not None:
             self.repository.setCurrentView(self.prevView)
             self.prevView = None

        self.callChain = False


    def execInView(self, method, *args, **kw):
        """
        This utility method will call C{AbstractRepositoryViewManager.setCurrentView}.
        Execute the method passed in as an argument and call
        C{AbstractRepositoryViewManager.restorePreviousView} when the method is finished executing.

        It abstracts the C{RepositoryView} switching logic for the caller and is the recommended means of
        executing code that utilizes a C{RepositoryView}.

        @param method: The method to execute
        @type method: a string
        @param args: Arguments to pass to the method
        @type args: list reference
        @param kw: Keyword dict to pass to the method
        @type args: dict reference
        @return: The value returned by the method call or None
        """

        result = None

        self.setViewCurrent()

        try:
            result = method(*args, **kw)

        finally:
            self.restorePreviousView()

        return result


    def execInViewThenCommit(self, method, *args, **kw):
        """
        This utility method will call C{AbstractRepositoryViewManager.setCurrentView},
        execute the method passed in as an argument and perform a Repository commit in
        the current Thread then call C{AbstractRepositoryViewManager.restorePreviousView}.

        It abstracts the C{RepositoryView} switching and commit logic for the caller and
        is the recommended means of executing a method and inline commit in a C{RepositoryView}.

        @param method: The method to execute
        @type method: a string
        @param args: Arguments to pass to the method
        @type args: list reference
        @param kw: Keyword dict to pass to the method
        @type args: dict reference
        @return: The value returned by the method call or None
        """
        result = None

        self.setViewCurrent()

        try:
            result = method(*args, **kw)
            self.__commit()
        finally:
            self.restorePreviousView()

        return result

    def execInViewThenCommitInThread(self, method, *args, **kw):
        """
        This utility method will call C{AbstractRepositoryViewManager.setCurrentView},
        execute the method passed in as an argument, spawn a C{RepositoryThread} to perform
        a Repository commit, then call C{AbstractRepositoryViewManager.restorePreviousView}. 
        Spawning a C{RepositoryThread}prevents the current Thread from blocking which the 
        C{RepositoryView} is commiting. This is especially useful
        when a Asynchronous model is employed.

        The method abstracts the C{RepositoryView} switching and commit logic for the caller and
        is the recommended means of executing a method and non-blocking commit in a C{RepositoryView}.

        @param method: The method to execute
        @type method: a string
        @param args: Arguments to pass to the method
        @type args: list reference
        @param kw: Keyword dict to pass to the method
        @type args: dict reference
        @return: The value returned by the method call or None
        """

        result = self.execInView(method, *args, **kw)
        self.commitInView(True)
        return result

    def getCurrentView(self):
        """
        Gets the current C{RepositoryView} the C{Repository} is working with
        @return: C{RepositoryView}
        """

        return self.repository.getCurrentView(False)

    def printCurrentView(self, printString = None):
        """
        Writes the current C{RepositoryView} as well as optional printString to the C{logging.Logger}
        instance. This method is useful for C{RepositoryView} debugging.

        @param printString: An optional string to display with the message (i.e. the name of the calling method)
        @type printString: string
        @return: C{None}
        """

        str = None

        if printString is None:
             self.log.info("Current View is: %s" % self.getCurrentView())
        else:
             self.log.info("[%s] Current View is: %s" % (printString, self.getCurrentView()))


    def commitInView(self, useThread=False):
        """
        Runs a C{RepositoryView} commit. If the commit is successful calls the
        C{AbstractRepositoryViewManager._viewCommitSuccess} method otherwise calls
        the C{AbstractRepositoryViewManager._viewCommitFailed} method. Both methods
        can be subclassed to add additional functionality. An optional useThread
        argument can be passed which indicates to run the commit in a dedicated
        C{RepositoryThread} to prevent blocking the current thread.

        @param useThread: Flag to indicate whether to run the view commit in the current
                          thread or a dedicated C{RepositoryThread} to prevent blocking
        @type: boolean
        @return: C{None}
        """

        if useThread:
            thread = RepositoryThread(target=self.__commitInView)
            thread.start()

        else:
            self.__commitInView

    def _viewCommitSuccess(self):
         """
         Called by C{AbstractRepositoryViewManager.commitView} when a
         C{RepositoryView} is commited.

         Overide this method to handle any additional functionality needed
         when a C{RepositoryView} is committed.
         @return: C{None}
         """

         pass

    def _viewCommitFailed(self, err):
         """
         Called by C{AbstractRepositoryViewManager.commitView} when a
         C{RepositoryView} raises an error on commited.

         Overide this method to handle any additional functionality needed
         when a C{RepositoryView} fails on commit.

         @param err: A Python Exception instance to use for debugging and error message display
         @type Exception

         @return: C{None}
         """
         str = "View Commit Failed: %s" % err
         self.log.error(str)

    def __commitInView(self):
        """
        Sets the current view then Attempts to commit the view.
        Calls viewCommitSuccess or viewCommitFailed. Then restore the 
        previous view. Need to sync with Andi on
        what happens in the case of a conflict or
        failed commit. This is still being resolved
        by the repository team
        """

        self.setViewCurrent()

        try:
            self.__commit()

        finally:
            self.restorePreviousView()

    def __commit(self):
        """
        Attempts to commit in the view. Calls viewCommitSuccess or
        viewCommitFailed.  This method does not set or unset the current 
        view.  Need to sync with Andi on
        what happens in the case of a conflict or
        failed commit. This is still being resolved
        by the repository team
        """

        try:
           self.view.commit()

        except VersionConflictError, e1:
           """This condition needs to be flushed out more"""
           self._viewCommitFailed(e1)

        except RepositoryError, e:
           """This condition needs to be flushed out more"""
           self._viewCommitFailed(e)

        except Exception, e2:
           """Catch any unknown exceptions raised by the Repository"""
           self._viewCommitFailed(e2)

        else:
           self._viewCommitSuccess()

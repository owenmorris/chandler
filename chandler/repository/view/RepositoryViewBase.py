__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import threading
import repository.persistence.RepositoryError as RepositoryError
import logging as logging


class RepositoryViewBase(object): 

    def __init__(self, viewName = None):
        """
        Base Class for View Context Management.

        @param viewName: The name to assign as the key for the view
        @type name: a string
        """
        self.view = Globals.repository.createView(viewName)
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

        log = logging.getLogger("RepositoryView")
        log.setLevel(logging.DEBUG)
        return log

    def setViewCurrent(self):
        """
        This method changes the view to one created by the C{RepositoryViewBase}

        It saves the previous view. Calling C{RepositoryViewBase.restorePreviousView} will
        restore the previous view as the current view.
        """

        assert self.callChain is False, "setViewCurrent called again before a restorePreviousView"

        assert self.prevView is None, "Nested prevView investigate"
        self.prevView = self.view.setCurrentView()
        self.callChain = True


    def restorePreviousView(self):
        """
        This method will restore the view that was current before C{RepositoryViewBase.setViewCurrent} was 
        called.

        The C{RepositoryViewBase.setViewCurrent} method must be called before this method otherwise there
        will be no view to restore.
        """

        assert self.callChain is True, "restorePreviousView called before calling setViewCurrent"

        if self.prevView is not None:
             Globals.repository.setCurrentView(self.prevView)
             self.prevView = None

        self.callChain = False


    def execInView(self, method, *args, **kw):
        """
        This is a utility method which will call C{RepositoryViewBase.setCurrentView} then
        execute the method passed in as an argument and finally call C{RepositoryViewBase.restorePreviousView}
        when the method is finished executing. 

        It abstracts the view switching logic for the caller and is recommended means to execute code in
        a view.

        @param method: The method to execute 
        @type method: a string
        @param args: Arguments to pass to the method
        @type args: list reference
        @param kw: Keyword dict to pass to the method
        @type args: dict reference 
        @return: C{None}
        """

        self.setViewCurrent()

        try:
            method(*args, **kw)

        finally:
            self.restorePreviousView()

    def getCurrentView(self):
        return Globals.repository.getCurrentView(False)

    def printCurrentView(self, printString = None):
        str = None

        if printString is None:
             self.log.info("Current View is: %s" % self.getCurrentView())
        else:
             self.log.info("[%s] Current View is: %s" % (printString, self.getCurrentView()))


    def commitView(self):
        """Runs a repository view commit in a thread to prevent blocking the 
           Twisted event loop. Commit resolution logic can be time consuming
           Let other Twisted events get processed while 
           the repository is handling the commit"""

        reactor.callInThread(self.__commitViewInThread)

    def _viewCommitSuccess(self):
         """Overide this method to handle any special cases required 
            after a view is committed. The default implementation will
            post the commit event back to the CPIA thread"""

         Globals.wxApplication.PostAsyncEvent(Globals.repository.commit)

    # Called from Thread
    def _viewCommitFailed(self):
         """If the commit failed then conflicts must be resolved.
            Overide this method to handle resolution logic"""

         self.log.error("ViewCommitFailed")

    def __commitViewInThread(self):
        """Tries to commit the view and call viewCommitSuccess or 
           viewCommitFailed.  Need to sync with Andi on
           what happens in the case of a conflict or 
           failed commit. This is still being resolved 
           by the repository team """

        self.setViewCurrent()

        try:
           self.view.commit()

        except RepositoryError:
           """This condition needs to be flushed out more"""
           self._viewCommitFailed()

        else:
           self._viewCommitSuccess()

        self.restorePreviousView()

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.persistence.RepositoryView as RepositoryView

class RepositoryViewManager(RepositoryView.AbstractRepositoryViewManager):

    def execInViewDeferred(self, result, method, *args, **kw):
        """
        This utility method will call C{AbstractRepositoryViewManager.execInView}.

        It abstracts the C{RepositoryView} switching logic for the caller and is the recommended means of
        executing code that utilizes a C{RepositoryView} with in a Twisted C{defer.Deferred}.

        a C{defer.Deferred} callback or errback returns as the first argument the result of the action
        then any additional arguments. This method reorders the argument list so that the method name is the 
        first argument then calls C{AbstractRepositoryViewManager.execInView}.

        @param result: The result of a callback or errorback
        @type result: Unknown
        @param method: The method to execute
        @type method: a string
        @param args: Arguments to pass to the method
        @type args: list reference
        @param kw: Keyword dict to pass to the method
        @type args: dict reference
        @return: The value returned by the method call or None
        """

        return super(RepositoryViewManager, self).execInView(method, result, *args, **kw)

    def execInViewThenCommitDeferred(self, result, method, *args, **kw):
        """
        This utility method will call C{AbstractRepositoryViewManager.execInViewThenCommit}.

        It abstracts the C{RepositoryView} switching logic for the caller and is the recommended means of
        executing code that utilizes a C{RepositoryView} with in a Twisted C{defer.Deferred}.

        a C{defer.Deferred} callback or errback returns as the first argument the result of the action
        then any additional arguments. This method reorders the argument list so that the method name is the
        first argument then calls C{AbstractRepositoryViewManager.execInViewThenCommit}.

        @param result: The result of a callback or errorback
        @type result: Unknown
        @param method: The method to execute
        @type method: a string
        @param args: Arguments to pass to the method
        @type args: list reference
        @param kw: Keyword dict to pass to the method
        @type args: dict reference
        @return: The value returned by the method call or None
        """

        return super(RepositoryViewManager, self).execInViewThenCommit(method, result, *args, **kw)

    def execInViewThenCommitInThreadDeferred(self, result, method, *args, **kw):
        """
        This utility method will call C{AbstractRepositoryViewManager.execInViewThenCommitInThread}.

        It abstracts the C{RepositoryView} switching logic for the caller and is the recommended means of
        executing code that utilizes a C{RepositoryView} with in a Twisted C{defer.Deferred}.

        a C{defer.Deferred} callback or errback returns as the first argument the result of the action
        then any additional arguments. This method reorders the argument list so that the method name is the
        first argument then calls C{AbstractRepositoryViewManager.execInViewThenCommitInThread}.

        @param result: The result of a callback or errorback
        @type result: Unknown
        @param method: The method to execute
        @type method: a string
        @param args: Arguments to pass to the method
        @type args: list reference
        @param kw: Keyword dict to pass to the method
        @type args: dict reference
        @return: The value returned by the method call or None
        """
        return super(RepositoryViewManager, self).execInViewThenCommitInThread(method, result, *args, **kw)


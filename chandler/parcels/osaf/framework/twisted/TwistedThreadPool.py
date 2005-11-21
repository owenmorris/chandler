import twisted.python.threadable as threadable
import twisted.python.threadpool as threadpool
import repository.persistence.Repository as Repository
import Queue

threadable.init()

class RepositoryThreadPool(threadpool.ThreadPool):
    """
       An extension of the Twisted Thread Pool class that leverages
       a C{RepositoryThread} instead of the standard python C{Thread}
    """

    def startAWorker(self):
        """
        Creates a worker thread of type C{RepositoryThread}
        """

        self.workers = self.workers + 1
        name = "RepositoryPoolThread-%s-%s" % (id(self), self.workers)
        try:
            firstJob = self.q.get(0)
        except Queue.Empty:
            firstJob = None
        newThread = Repository.RepositoryThread(target=self._worker, name=name, args=(firstJob,))
        self.threads.append(newThread)
        newThread.start()

import twisted.python.threadable as threadable
import twisted.python.threadpool as threadpool
import repository.persistence.Repository as Repository
import application.Globals as Globals
import Queue

threadable.init()

class RepositoryThreadPool(threadpool.ThreadPool):
    """
       An extension of the Twisted Thread Pool class that leverages
       a C{RepositoryThread} instead of the standard python C{Thread}
    """

    def startAWorker(self):
        self.workers = self.workers + 1
        name = "PoolThread-%s-%s" % (id(self), self.workers)
        try:
            firstJob = self.q.get(0)
        except Queue.Empty:
            firstJob = None
        newThread = Repository.RepositoryThread(Globals.repository, target=self._worker, name=name, args=(firstJob,))
        self.threads.append(newThread)
        newThread.start()

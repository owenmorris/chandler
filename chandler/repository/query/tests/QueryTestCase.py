import os, unittest
import repository.tests.RepositoryTestCase as RepositoryTestCase
import repository.query.Query as Query

class QueryTestCase(RepositoryTestCase.RepositoryTestCase):
    
    def setUp(self):
        RepositoryTestCase.RepositoryTestCase._setup(self, False)

        self.testdir = os.path.join(self.rootdir, 'chandler', 'repository', \
         'query', 'tests')
        RepositoryTestCase.RepositoryTestCase._openRepository(self, False)

    def _executeQuery(self, queryString, args=None):
        q = Query.Query(self.rep, queryString)
        if args is not None:
            q.args = args
        q.execute()
        return q

    def _printQuery(self, query):
        q = self._executeQuery(query)
        for i in q:
            print i

    def _checkQuery(self,expr,results):
        for i in results:
            self.failIf(expr(i))

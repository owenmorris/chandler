import os, unittest
import repository.tests.RepositoryTestCase as RepositoryTestCase
import repository.query.Query as Query

class QueryTestCase(RepositoryTestCase.RepositoryTestCase):
    
    def setUp(self):
        RepositoryTestCase.RepositoryTestCase._setup(self, True)

        self.testdir = os.path.join(self.rootdir, 'repository', \
         'query', 'tests')
        RepositoryTestCase.RepositoryTestCase._openRepository(self, True)

    def _compileQuery(self, name, queryString, args=None):
        p = self.rep.findPath('//Queries')
        k = self.rep.findPath('//Schema/Core/Query')
        q = Query.Query(name, p, k, queryString)
        if args is not None:
            q.args = args
#        q.compile()
        return q

    def _printQuery(self, query):
        q = self._compileQuery(query)
        for i in q:
            print i

    def _checkQuery(self,expr,results):
        for i in results:
            self.failIf(expr(i))

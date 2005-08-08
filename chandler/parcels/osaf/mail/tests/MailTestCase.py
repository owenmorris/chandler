import unittest, os, sys

import repository.tests.RepositoryTestCase as RepositoryTestCase


class MailTestCase(RepositoryTestCase.RepositoryTestCase):

    __setup = False

    def setUp(self):

        if self.__setup:
            return

        self.__setup = True

        super(MailTestCase, self)._setup(self)

        self.testdir = os.path.join(self.rootdir, 'parcels', 'osaf',
         'pim', 'mail')

        super(MailTestCase, self)._openRepository(self)


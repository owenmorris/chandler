"""
A helper class which sets up and tears down a repository and anything else
that a parcel loader unit test might need
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os, sys

from repository.persistence.XMLRepository import XMLRepository
import repository.tests.RepositoryTestCase as RepositoryTestCase
import application.Globals as Globals

class ParcelLoaderTestCase(RepositoryTestCase.RepositoryTestCase):

    def setUp(self):
        super(ParcelLoaderTestCase,self)._setup(self)

        self.testdir = os.path.join(self.rootdir, 'chandler', 'repository',
         'parcel', 'tests')

        super(ParcelLoaderTestCase,self)._openRepository(self)
        Globals.repository = self.rep # to keep indexer happy

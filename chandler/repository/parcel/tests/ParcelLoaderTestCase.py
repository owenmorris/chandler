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
import application.Globals as Globals

class ParcelLoaderTestCase(unittest.TestCase):

    def setUp(self):
        self.rootdir = os.environ['CHANDLERHOME']
        self.testdir = os.path.join(self.rootdir, 'Chandler', 'repository',
         'parcel', 'tests')
        self.rep = XMLRepository(os.path.join(self.testdir,'__repository__'))
        Globals.repository = self.rep # to keep indexer happy
        self.rep.create()
        schemaPack = os.path.join(self.rootdir, 'Chandler', 'repository',
         'packs', 'schema.pack')
        self.rep.loadPack(schemaPack)
        self.rep.commit()

    def tearDown(self):
        self.rep.close()
        self.rep.delete()

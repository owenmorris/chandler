"""
A helper class which sets up and tears down a repository and anything else
that a parcel loader unit test might need
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os, sys

import repository.tests.RepositoryTestCase as RepositoryTestCase

import application
import application.Globals as Globals

class ParcelLoaderTestCase(RepositoryTestCase.RepositoryTestCase):

    def setUp(self):

        super(ParcelLoaderTestCase, self)._setup(self)

        self.testdir = os.path.join(self.rootdir, 'application', 'tests')

        super(ParcelLoaderTestCase, self)._openRepository(self)

        view = self.rep.view
        Globals.parcelManager = application.Parcel.Manager.getManager(view)


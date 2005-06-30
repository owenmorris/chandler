"""
Unit tests for Location Items
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import osaf.contentmodel.tests.TestContentModel as TestContentModel
import osaf.contentmodel.calendar.Calendar as Calendar

from repository.util.Path import Path


class LocationsTest(TestContentModel.ContentModelTestCase):
    """ Test Locations Content Model """

    def testLocations(self):
        """ Simple test for the Locations Factory - getLocation """

        self.loadParcel("parcel:osaf.contentmodel.calendar")

        # Test the globals
        locationsPath = Path('//parcels/osaf/contentmodel/calendar')
        view = self.rep.view
        
        self.assertEqual(Calendar.Location.getKind(view),
                         view.find(Path(locationsPath, 'Location')))

        locationNames = ["Alderon", "Atlantis", "Arcadia"]

        # Construct sample items
        for loc in locationNames:
            # use the factory to create or lookup an item
            aRoom = Calendar.Location.getLocation (view, loc)
            # test that convert to string yeilds the name of the location
            self.assertEqual (loc, str (aRoom))

        # call the factory on the last name again, to ensure reuse
        sameLocation = Calendar.Location.getLocation (view, locationNames [-1])
        self.assert_ (aRoom is sameLocation, "Location factory failed to return the same location!")

        # Double check kinds
        self.assertEqual(aRoom.itsKind, Calendar.Location.getKind(view))

        # Literal properties
        aRoom.displayName = "A Nice Place" # change the Location name
        # make sure we can get the name, and find it by that name
        sameLocation = Calendar.Location.getLocation (view, aRoom.displayName)
        self.assert_ (aRoom is sameLocation, "Location factory failed to return an identical location!")


if __name__ == "__main__":
    unittest.main()

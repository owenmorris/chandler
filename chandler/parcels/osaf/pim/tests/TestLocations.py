#   Copyright (c) 2004-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Unit tests for Location Items
"""

import unittest, os

import osaf.pim.tests.TestDomainModel as TestDomainModel
import osaf.pim.calendar.Calendar as Calendar

from repository.util.Path import Path
from i18n.tests import uw


class LocationsTest(TestDomainModel.DomainModelTestCase):
    """ Test Locations Domain Model """

    def testLocations(self):
        """ Simple test for the Locations Factory - getLocation """

        self.loadParcel("osaf.pim.calendar")

        # Test the globals
        locationsPath = Path('//parcels/osaf/pim/calendar')
        view = self.rep.view

        self.assertEqual(Calendar.Location.getKind(view),
                         view.find(Path(locationsPath, 'Location')))

        locationNames = [uw("Alderon"), uw("Atlantis"), uw("Arcadia")]

        # Construct sample items
        for loc in locationNames:
            # use the factory to create or lookup an item
            aRoom = Calendar.Location.getLocation (view, loc)
            # test that convert to string yeilds the name of the location
            self.assertEqual (loc, unicode (aRoom))

        # call the factory on the last name again, to ensure reuse
        sameLocation = Calendar.Location.getLocation (view, locationNames [-1])
        self.assert_ (aRoom is sameLocation, "Location factory failed to return the same location!")

        # Double check kinds
        self.assertEqual(aRoom.itsKind, Calendar.Location.getKind(view))

        # Literal properties
        aRoom.displayName = uw("A Nice Place") # change the Location name
        # make sure we can get the name, and find it by that name
        sameLocation = Calendar.Location.getLocation (view, aRoom.displayName)
        self.assert_ (aRoom is sameLocation, "Location factory failed to return an identical location!")


if __name__ == "__main__":
    unittest.main()

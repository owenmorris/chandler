import unittest
from application import schema
from osaf import pim
from util import testcase

class TestUIDMap(testcase.NRVTestCase):

    def testMap(self):

        view = self.view

        uid_map = schema.ns('osaf.sharing', view).uid_map

        event1 = pim.CalendarEvent(view=view)

        # Creating an event sets its icalUID, which is monitored by uid_map,
        # which in turn adds the event to the 'items' ref collection using
        # the icalUID attribute value as an alias
        self.assertEqual(event1, uid_map.items.getByAlias(event1.icalUID))
        self.assertEqual(event1.icalUIDMap, uid_map)

        # Removing the item's icalUID attribute should also remove the item
        # from the uid_map
        del event1.icalUID
        self.assert_(event1 not in uid_map.items)

if __name__ == "__main__":
    unittest.main()

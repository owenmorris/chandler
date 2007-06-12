#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import os, wx, sys 
import osaf.pim.calendar.Calendar as Calendar
from osaf import sharing, pim
from i18n.tests import uw
import application.Globals as Globals

class TestImportOverwrite(ChandlerTestCase):

    def startTest(self):
        
        appView = self.app_ns.itsView

        # make user collection, since only user
        # collections can be displayed as a calendar
        col = QAUITestAppLib.UITestItem("Collection", self.logger)

        #create an event to export
        self.logger.startAction('Create event to export')
        event = QAUITestAppLib.UITestItem("Event", self.logger)
        event_UUID = event.item.itsUUID
        #write some stuff in the event to make it unique
        event.SetAttr(displayName=uw("Original Event"), startDate="01/01/2001", startTime="12:00 AM", body=uw("This is the original event"))
        self.logger.addComment("Created Event to Export")
    
        #export the event
        path = os.path.join(Globals.chandlerDirectory,"tools/cats/DataFiles")
        filename = 'tempOverwriteTest.ics'
        fullpath = os.path.join(path, filename)
        if os.path.exists(fullpath):
            os.remove(fullpath)
        #Upcast path to unicode since Sharing requires a unicode path
        fullpath = unicode(fullpath, sys.getfilesystemencoding())

        collection = pim.ListCollection(itsView=appView)
        # exporting all Events is VERY expensive, it doesn't seem like a good
        # way to test if events can be exported successfully.  Instead, just
        # export one event.
        #for tmpEvent in Calendar.EventStamp.getCollection(appView):
            #collection.add(tmpEvent)
        collection.add(event.item)
        sharing.exportFile(appView, fullpath, collection)
        application = wx.GetApp()
        application.Yield(True)
        self.logger.addComment("Exported event")
        
        #change the event after exporting
        event.SetAttr(displayName=uw("Changed Event"),  body=uw("This event has been changed"))
        self.logger.addComment("event changed after export")
    
        #import the original event
        sharing.importFile(appView, fullpath)
        application.Yield(True)
        self.logger.addComment("Imported exported event")
    
        #check if changed attributes have reverted to original values
            #find imported event by UUID
        self.logger.startAction("Verify event overwritten")
        found = self.app_ns.view.findUUID(event_UUID)
        if found.body == uw('This is the original event') and \
                     found.displayName == uw('Original Event'):
            self.logger.endAction(True, "Event overwriten")
        else:
            self.logger.endAction(False, 'Event not overwriten')


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

"""
Test that when an event that has been deleted is re-imported that it comes out of the trash 
and into the imported collection
"""
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import os, sys
from time import localtime, strftime
import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import osaf.framework.scripting as scripting
from application import Globals

class TestRemoveFromTrashOnImport(ChandlerTestCase):
    
    def startTest(self):
    
        appView = self.app_ns.itsView
        today = strftime('%m/%d/%y',localtime())
        
        colName = "deleteThenImport"
        eventName = "eventToTest"

        #create a collection
        collection = QAUITestAppLib.UITestItem("Collection", self.logger)
        # SetDisplayName fails after TestEventStacking occluded its collection
        # by adding events that appeared in the PreviewArea (bug 6727).  To work
        # around this, just set collection's displayName directly for now.
        # This is a brittle hack, the failure is order-dependent.  We need a
        # more robust solution to the sidebar SetDisplayName failures.
        #collection.SetDisplayName(colName)
        collection.item.displayName = colName 
        sb=self.app_ns.sidebar
        scripting.User.emulate_sidebarClick(sb,colName) 
        
        #create an event
        ev=QAUITestAppLib.UITestItem('Event', self.logger)
        ev.SetAttr(displayName=eventName, startDate=today, startTime="12:00 PM")
        
        #create a path to export to
        reportDir = Globals.options.profileDir
        fullpath = os.path.join(reportDir,colName)
        if os.path.exists(fullpath):
            os.remove(fullpath)
        reportDir = unicode(reportDir, sys.getfilesystemencoding())
        
        #export
        share = Sharing.OneTimeFileSystemShare(reportDir, u'deleteThenImport.ics', ICalendar.ICalendarFormat, itsView=appView)
        share.contents = collection.item
        share.put()
        
        #delete collection
        scripting.User.emulate_sidebarClick(sb,colName) 
        collection.DeleteCollection()
        
        #import event back in
        share = Sharing.OneTimeFileSystemShare(reportDir, u'deleteThenImport.ics', ICalendar.ICalendarFormat, itsView=appView)
        collection = share.get()
        self.app_ns.sidebarCollection.add(collection)
        scripting.User.idle()    
            
        #verify
        ev.Check_ItemInCollection("Trash", expectedResult=False)
        ev.Check_ItemInCollection(colName, expectedResult=True)
            

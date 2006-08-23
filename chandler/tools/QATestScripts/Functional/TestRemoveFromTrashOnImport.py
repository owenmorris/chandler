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
import tools.QAUITestAppLib as QAUITestAppLib
import os, sys
from time import localtime, strftime
import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import osaf.framework.scripting as scripting
from application import Globals

appView = app_ns().itsView
App_ns = app_ns()
today = strftime('%m/%d/%y',localtime())

#initialization
fileName = "TestRemoveFromTrashOnImport.log"
logger = QAUITestAppLib.QALogger(fileName, "TestRemoveFromTrashOnImport")
colName = "deleteThenImport"
eventName = "eventToTest"

try:
    #create a collection
    collection = QAUITestAppLib.UITestItem("Collection", logger)
    collection.SetDisplayName(colName)
    sb=App_ns.sidebar
    scripting.User.emulate_sidebarClick(sb,colName) 
    
    #create an event
    ev=QAUITestAppLib.UITestItem('Event', logger)
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
    App_ns.sidebarCollection.add(collection)
    User.idle()    
        
    #verify
    ev.Check_ItemInCollection("Trash", expectedResult=False)
    ev.Check_ItemInCollection(colName, expectedResult=True)
        
finally:
    #cleaning
    logger.Close()

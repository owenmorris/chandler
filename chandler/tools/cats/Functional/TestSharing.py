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
import os, sys
from application.dialogs.PublishCollection import ShowPublishDialog
import wx
from i18n import ChandlerMessageFactory as _
from osaf.sharing import Sharing, unpublish 
import osaf.sharing.ICalendar as ICalendar
import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import osaf.pim as pim
from i18n.tests import uw
from osaf.framework.blocks.Block import Block
from repository.item.Item import MissingClass


class TestSharing(ChandlerTestCase):

    def startTest(self):

        # action
        # Webdav Account Setting
        ap = QAUITestAppLib.UITestAccounts(self.logger)
        ap.Open() # first, open the accounts dialog window
        ap.CreateAccount("WebDAV")
        ap.TypeValue("displayName", uw("Sharing Test WebDAV"))
        ap.TypeValue("host", "qacosmo.osafoundation.org")
        ap.TypeValue("path", "cosmo/home/demo1")
        ap.TypeValue("username", "demo1")
        ap.TypeValue("password", "ad3leib5")
        ap.TypeValue("port", "8080")
        ap.ToggleValue("ssl", False)
        ap.ToggleValue("default", True)
        ap.Ok()
    
        # verification
        ap.VerifyValues("WebDAV", uw("Sharing Test WebDAV"), host = "qacosmo.osafoundation.org", username = "demo1", password="ad3leib5", port=8080)
        
        # import events so test will have something to share even when run by itself
        path = os.path.join(os.getenv('CHANDLERHOME'),"tools/cats/DataFiles")
        # Upcast path to unicode since Sharing requires a unicode path
        path = unicode(path, sys.getfilesystemencoding())
        share = Sharing.OneTimeFileSystemShare(path, u'testSharing.ics', ICalendar.ICalendarFormat, itsView=self.app_ns.itsView)
        
        self.logger.startAction(name="Import testSharing Calendar")
        collection = share.get()
        self.app_ns.sidebarCollection.add(collection)
        self.scripting.User.idle()
        self.logger.endAction(True)
    
        
        # Collection selection
        sidebar = self.app_ns.sidebar
        QAUITestAppLib.scripting.User.emulate_sidebarClick(sidebar, "testSharing")
        
        # Sharing dialog
        self.logger.startAction("Sharing dialog")
        collection = Block.findBlockByName("MainView").getSidebarSelectedCollection()
        if collection is not None:
            if sidebar.filterClass is MissingClass:
                filterClassName = None 
            else:
                klass = sidebar.filterClass
                filterClassName = "%s.%s" % (klass.__module__, klass.__name__)
            win = ShowPublishDialog(wx.GetApp().mainFrame, view=self.app_ns.itsView,
                                    collection=collection,
                                    filterClassName=filterClassName,
                                    modal=False)
            #Share button call
            
            win.PublishCollection()
 
            while not win.done:
                wx.GetApp().Yield()
 
            if not win.success:
                self.logger.ReportFailure("(On publish collection)")
 
            #Done button call
            win.OnPublishDone(None)
            wx.GetApp().Yield()
            # cleanup
            # cosmo can only handle so many shared calendars
            # so remove this one when done
            # Note: We don't need a try: here if this raises, the
            # test has already reported success.
            unpublish(collection) 
        else:
            self.logger.endAction(False, 'collection is None')
            
        self.logger.endAction(True)
        
        

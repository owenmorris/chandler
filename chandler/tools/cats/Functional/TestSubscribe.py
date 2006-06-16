import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import os
import application.dialogs.SubscribeCollection as SubscribeCollection
import wx
from i18n.tests import uw
import osaf.framework.scripting as scripting


class TestSubscribing(ChandlerTestCase):

    def startTest(self):

        # action
        # Webdav Account Setting
        ap = QAUITestAppLib.UITestAccounts(self.logger)
        ap.Open() # first, open the accounts dialog window
        ap.CreateAccount("WebDAV")
        ap.TypeValue("displayName", uw("Subscribe Test WebDAV"))
        ap.TypeValue("host", "qacosmo.osafoundation.org")
        ap.TypeValue("path", "home/demo1")
        ap.TypeValue("username", "demo1")
        ap.TypeValue("password", "ad3leib5")
        ap.TypeValue("port", "8080")
        ap.ToggleValue("ssl", False)
        ap.ToggleValue("default", True)
        ap.Ok()
        self.logger.endAction(True)
    
        # verification
        ap.VerifyValues("WebDAV", uw("Subscribe Test WebDAV"), displayName = uw("Subscribe Test WebDAV"), host = "qacosmo.osafoundation.org", path = "home/demo1", username = "demo1", password="ad3leib5", port=8080)

        # Subscribe dialog
        self.logger.startAction("Subscribe dialog")
        window = SubscribeCollection.Show(wx.GetApp().mainFrame,
            view=self.app_ns.itsView, modal=False)
        window = wx.FindWindowByLabel("Subscribe to Shared Collection")
        url = window.toolPanel.GetChildren()[1]
        url.SetFocus()
        url.Clear()
        QAUITestAppLib.scripting.User.emulate_typing("http://qacosmo.osafoundation.org:8080/home/demo1/importTest-1?ticket=g0kplikch1")
        window.OnSubscribe(None)
        scripting.User.idle()
    
        # verification
        if QAUITestAppLib.scripting.User.emulate_sidebarClick(App_ns.sidebar, "importTest"):
            self.logger.endAction(True, "(On Subscribe collection)")
        else:
            self.logger.endAction(False, "(On Subscribe collection)")
    


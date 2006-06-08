import tools.QAUITestAppLib as QAUITestAppLib
import os
import application.dialogs.SubscribeCollection as SubscribeCollection
import wx
from i18n.tests import uw

App_ns = app_ns()

#initialization
fileName = "PerfSubscribe.log"
logger = QAUITestAppLib.QALogger(fileName, "PerfSubscribe")

try:
    # action
    # Webdav Account Setting
    ap = QAUITestAppLib.UITestAccounts(logger)
    ap.Open() # first, open the accounts dialog window
    ap.CreateAccount("WebDAV")
    displayName = uw("Subscribe Test WebDAV")
    ap.TypeValue("displayName", displayName)
    ap.TypeValue("host", "qacosmo.osafoundation.org")
    ap.TypeValue("path", "home/demo1")
    ap.TypeValue("username", "demo1")
    ap.TypeValue("password", "ad3leib5")
    ap.TypeValue("port", "8080")
    ap.ToggleValue("ssl", False)
    ap.ToggleValue("default", True)
    ap.Ok()

    # verification
    ap.VerifyValues("WebDAV", displayName, displayName = displayName, host = "qacosmo.osafoundation.org", path = "home/demo1", username = "demo1", password="ad3leib5", port=8080)

    # Subscribe dialog
    window = SubscribeCollection.Show(wx.GetApp().mainFrame,
        view=App_ns.itsView, modal=False)
    window = wx.FindWindowByLabel("Subscribe to Shared Collection")
    url = window.toolPanel.GetChildren()[1]
    url.SetFocus()
    url.Clear()
    
    # XXX Need to find a way to create the collection as part part of this
    # XXX test rather than rely on externally created collection.
    QAUITestAppLib.scripting.User.emulate_typing("http://qacosmo.osafoundation.org:8080/cosmo/home/demo1/testSharing/?ticket=bqmhfb4510")

    # We are interested in seeing how quickly we can download the collection
    logger.Start('Subscribe')
    window.OnSubscribe(None)
    logger.Stop()
    
    User.idle()

    # verification
    if QAUITestAppLib.scripting.User.emulate_sidebarClick(App_ns.sidebar, "testSharing"):
        logger.ReportPass("(On Subscribe collection)")
    else:
        logger.ReportFailure("(On Subscribe collection)")
    logger.SetChecked(True)

finally:
    #cleaning
    logger.Report("Subscribe")
    logger.Close()

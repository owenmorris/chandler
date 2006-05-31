import tools.QAUITestAppLib as QAUITestAppLib
import os
import application.dialogs.SubscribeCollection as SubscribeCollection
import wx
from i18n.tests import uw

App_ns = app_ns()

#initialization
fileName = "TestSubscribe.log"
logger = QAUITestAppLib.QALogger(fileName, "TestSubscribe")

try:
    # action
    # Webdav Account Setting
    logger.Start("WebDAV account setting")
    ap = QAUITestAppLib.UITestAccounts(logger)
    ap.Open() # first, open the accounts dialog window
    ap.CreateAccount("WebDAV")
    ap.TypeValue("displayName", uw("Subscribe Test WebDAV"),
    ap.TypeValue("host", "qacosmo.osafoundation.org")
    ap.TypeValue("path", "home/demo1")
    ap.TypeValue("username", "demo1")
    ap.TypeValue("password", "ad3leib5")
    ap.TypeValue("port", "8080")
    ap.ToggleValue("ssl", False)
    ap.ToggleValue("default", True)
    ap.Ok()
    logger.Stop()

    # verification
    ap.VerifyValues("WebDAV", uw("Subscribe Test WebDAV"), displayName = uw("Subscribe Test WebDAV"), host = "qacosmo.osafoundation.org", path = "home/demo1", username = "demo1", password="ad3leib5", port=8080)

    # Subscribe dialog
    logger.Start("Subscribe dialog")
    window = SubscribeCollection.Show(wx.GetApp().mainFrame,
        view=App_ns.itsView, modal=False)
    window = wx.FindWindowByLabel("Subscribe to Shared Collection")
    url = window.toolPanel.GetChildren()[1]
    url.SetFocus()
    url.Clear()
    QAUITestAppLib.scripting.User.emulate_typing("http://qacosmo.osafoundation.org:8080/home/demo1/importTest-1?ticket=g0kplikch1")
    window.OnSubscribe(None)
    User.idle()
    logger.Stop()

    # verification
    logger.SetChecked(True)
    if QAUITestAppLib.scripting.User.emulate_sidebarClick(App_ns.sidebar, "importTest"):
        logger.ReportPass("(On Subscribe collection)")
    else:
        logger.ReportFailure("(On Subscribe collection)")

    # report the results from checking
    logger.Report("Sidebar")

finally:
    #cleaning
    logger.Close()

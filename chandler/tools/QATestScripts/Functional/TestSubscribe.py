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
    url = window.toolPanel.GetChildren()[1]
    url.SetFocus()
    url.Clear()
    QAUITestAppLib.scripting.User.emulate_typing("http://qacosmo.osafoundation.org:8080/home/demo1/importTest-1?ticket=g0kplikch1")
    window.OnSubscribe(None)
    User.idle()

    # verification
    if QAUITestAppLib.scripting.User.emulate_sidebarClick(App_ns.sidebar, "importTest"):
        logger.ReportPass("(On Subscribe collection)")
    else:
        logger.ReportFailure("(On Subscribe collection)")
    logger.SetChecked(True)

finally:
    #cleaning
    logger.Report("Subscribe")
    logger.Close()

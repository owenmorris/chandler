import tools.QAUITestAppLib as QAUITestAppLib
import os
import application.dialogs.SubscribeCollection as SubscribeCollection
import application.Globals as Globals
import wx
from i18n import OSAFMessageFactory as _

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
    ap.TypeValue("displayName", "Subscribe Test WebDAV")
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
    ap.VerifyValues("WebDAV", "Subscribe Test WebDAV", displayName = "Subscribe Test WebDAV", host = "qacosmo.osafoundation.org", username = "demo1",
                    password="ad3leib5", port=8080)
    
    # Subscribe dialog
    logger.Start("Subscribe dialog")
    xrcFile = os.path.join(Globals.chandlerDirectory, 'application', 'dialogs', 'SubscribeCollection_wdr.xrc')
    resources = wx.xrc.XmlResource(xrcFile)
    win = SubscribeCollection.SubscribeDialog(wx.GetApp().mainFrame, _("Subscribe to Shared Collection"), resources=resources, view=App_ns.itsView, url=None)
    win.CenterOnScreen()
    win.Show()
    wx.GetApp().Yield()
    window = wx.FindWindowByLabel("Subscribe to Shared Collection")
    url = window.toolPanel.GetChildren()[1]
    url.SetFocus()
    url.Clear()
    wx.GetApp().Yield()
    QAUITestAppLib.scripting.User.emulate_typing("webcal://qacosmo.osafoundation.org:8080/home/demo1/importTest.ics")
    window.OnSubscribe(None)
    win.Destroy()
    wx.GetApp().Yield()
    ev = wx.IdleEvent()
    wx.GetApp().ProcessEvent(ev)
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

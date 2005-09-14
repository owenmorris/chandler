import util.QAUITestAppLib as QAUITestAppLib
import os
import application.dialogs.PublishCollection as PublishCollection
import application.Globals as Globals
import wx
from i18n import OSAFMessageFactory as _

App_ns = QAUITestAppLib.App_ns

filePath = os.getenv('CATSREPORTDIR')
if not filePath:
    filePath = os.getcwd()

#initialization
fileName = "TestSharing.log"
logger = QAUITestAppLib.QALogger(os.path.join(filePath, fileName),"TestSharing")

#action
#Webdav Account Setting
logger.Start("WebDAV account setting")
ap = QAUITestAppLib.UITestAccounts(logger)
ap.Open() # first, open the accounts dialog window
ap.CreateAccount("WebDAV")
ap.TypeValue("displayName", "Sharing Test WebDAV")
ap.TypeValue("host", "qacosmo.osafoundation.org")
ap.TypeValue("path", "home/demo1")
ap.TypeValue("username", "demo1")
ap.TypeValue("password", "ad3leib5")
ap.TypeValue("port", "8080")
ap.ToggleValue("ssl", False)
ap.ToggleValue("default", True)
ap.Ok()
logger.Stop()
#verification
ap.VerifyValues("WebDAV", "Sharing Test WebDAV", displayName = "Sharing Test WebDAV", host = "qacosmo.osafoundation.org", username = "demo1",
                password="ad3leib5", port=8080)


sidebar = App_ns.sidebar
#Collection selection
QAUITestAppLib.scripting.User.emulate_sidebarClick(sidebar, "All")

#Sharing dialog
logger.Start("Sharing dialog")
collection = Globals.views[0].getSidebarSelectedCollection()
if collection is not None:
    if sidebar.filterKind is None:
        filterKindPath = None 
    else:
        filterKindPath = str(sidebar.filterKind.itsPath)
    xrcFile = os.path.join(Globals.chandlerDirectory, 'application', 'dialogs', 'PublishCollection_wdr.xrc')
    resources = wx.xrc.XmlResource(xrcFile)
    win = PublishCollection.PublishCollectionDialog(wx.GetApp().mainFrame, _("Collection Sharing"),resources=resources, view=App_ns.itsView,
                                                    collection=collection, filterKindPath=filterKindPath)
    win.CenterOnScreen()
    win.Show()
    #Share button call
    win.OnPublish(None)
    #Done button call
    win.OnPublishDone(None)
    win.Destroy()
    wx.GetApp().Yield()
    logger.Stop()

#cleaning
logger.Close()

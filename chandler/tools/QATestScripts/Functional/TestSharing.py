import tools.QAUITestAppLib as QAUITestAppLib
import os
from application.dialogs.PublishCollection import ShowPublishDialog
import application.Globals as Globals
import wx
from i18n import OSAFMessageFactory as _

App_ns = app_ns()

# initialization
fileName = "TestSharing.log"
logger = QAUITestAppLib.QALogger(fileName, "TestSharing")
    
try:
    # action
    # Webdav Account Setting
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

    # verification
    ap.VerifyValues("WebDAV", "Sharing Test WebDAV", displayName = "Sharing Test WebDAV", host = "qacosmo.osafoundation.org", username = "demo1",
                    password="ad3leib5", port=8080)
    
    # Collection selection
    sidebar = App_ns.sidebar
    QAUITestAppLib.scripting.User.emulate_sidebarClick(sidebar, "All")
    
    # Sharing dialog
    logger.Start("Sharing dialog")
    collection = Globals.views[0].getSidebarSelectedCollection()
    if collection is not None:
        if sidebar.filterKind is None:
            filterClassName = None 
        else:
            klass = sidebar.filterKind.classes['python']
            filterClassName = "%s.%s" % (klass.__module__, klass.__name__)
        win = ShowPublishDialog(wx.GetApp().mainFrame, view=App_ns.itsView,
                                collection=collection,
                                filterClassName=filterClassName,
                                modal=False)
        #Share button call
        if not win.OnPublish(None):
            logger.ReportFailure("(On publish collection)")
        #Done button call
        win.OnPublishDone(None)
        wx.GetApp().Yield()
        logger.SetChecked(True)
        logger.Report("Sharing dialog")
        logger.Stop()

finally:
    # cleaning
    logger.Close()

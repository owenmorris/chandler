import tools.QAUITestAppLib as QAUITestAppLib
import os, sys
from application.dialogs.PublishCollection import ShowPublishDialog
import application.Globals as Globals
import wx
from i18n import OSAFMessageFactory as _
import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar
import tools.QAUITestAppLib as QAUITestAppLib
import osaf.pim as pim

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
    ap.TypeValue("path", "cosmo/home/demo1")
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
    
    
    # import events so test will have something to share even when run by itself
    path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
    # Upcast path to unicode since Sharing requires a unicode path
    path = unicode(path, sys.getfilesystemencoding())
    share = Sharing.OneTimeFileSystemShare(path, u'500Events.ics', ICalendar.ICalendarFormat, itsView=App_ns.itsView)
    
    logger.Start("Import 500 event Calendar")
    try:
        collection = share.get()
    except:
        logger.Stop()
        logger.ReportFailure("Importing calendar: exception raised")
    else:
        App_ns.sidebarCollection.add(collection)
        User.idle()
        logger.Stop()
        logger.ReportPass("Importing calendar")
    
    
    # Collection selection
    # at SVN REV 10217 this does not work
    sidebar = App_ns.sidebar
    QAUITestAppLib.scripting.User.emulate_sidebarClick(sidebar, "500Events")
    
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

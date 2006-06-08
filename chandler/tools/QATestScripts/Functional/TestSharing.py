import tools.QAUITestAppLib as QAUITestAppLib
import os
from application.dialogs.PublishCollection import ShowPublishDialog
import wx
from i18n import OSAFMessageFactory as _
from osaf.sharing import Sharing, unpublish 
import osaf.sharing.ICalendar as ICalendar
import tools.QAUITestAppLib as QAUITestAppLib
import osaf.pim as pim
from i18n.tests import uw
from osaf.framework.blocks.Block import Block

App_ns = app_ns()

# initialization
fileName = "TestSharing.log"
logger = QAUITestAppLib.QALogger(fileName, "TestSharing")

try:
    # action
    # Webdav Account Setting
    ap = QAUITestAppLib.UITestAccounts(logger)
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
    ap.VerifyValues("WebDAV", uw("Sharing Test WebDAV"), displayName = uw("Sharing Test WebDAV"), host = "qacosmo.osafoundation.org", username = "demo1", password="ad3leib5", port=8080)

    # import events so test will have something to share even when run by itself
    path = os.path.join(os.getenv('CHANDLERHOME'),"tools/QATestScripts/DataFiles")
    # Upcast path to unicode since Sharing requires a unicode path
    path = unicode(path, 'utf8')
    share = Sharing.OneTimeFileSystemShare(path, u'testSharing.ics', ICalendar.ICalendarFormat, itsView=App_ns.itsView)

    collection = share.get()
    App_ns.sidebarCollection.add(collection)
    User.idle()

    # Collection selection
    sidebar = App_ns.sidebar
    QAUITestAppLib.scripting.User.emulate_sidebarClick(sidebar, "testSharing")

    # Sharing dialog
    collection = Block.findBlockByName("MainView").getSidebarSelectedCollection()
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

        # cleanup
        # cosmo can only handle so many shared calendars
        # so remove this one when done
        # Note: We don't need a try: here if this raises, the
        # test has already reported success.
        unpublish(collection)

finally:
    # cleaning
    logger.Report('Sharing')
    logger.Close()

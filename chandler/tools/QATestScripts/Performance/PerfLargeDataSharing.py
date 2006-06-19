import tools.QAUITestAppLib as QAUITestAppLib
import os
from application.dialogs.PublishCollection import ShowPublishDialog
import application.dialogs.SubscribeCollection as SubscribeCollection
import wx
from i18n import OSAFMessageFactory as _
from osaf.sharing import Sharing, unpublish 
from osaf import sharing
import osaf.sharing.ICalendar as ICalendar
import tools.QAUITestAppLib as QAUITestAppLib
import osaf.pim as pim
from i18n.tests import uw
from osaf.framework.blocks.Block import Block

App_ns = app_ns()


def sidebarCollectionNamed(name):
    """
    Look for a sidebar collection with name, otherwise return None
    """
    sidebarWidget = app_ns().sidebar.widget
    for i in range(sidebarWidget.GetNumberRows()):
        collection = sidebarWidget.GetTable().GetValue(i,0)[0]
        if collection.displayName == name:
            return collection
    return None

# initialization
fileName = "PerfLargeDataSharing.log"
logger = QAUITestAppLib.QALogger(fileName, "PerfLargeDataSharing")

try:
    # action
    # Webdav Account Setting
    ap = QAUITestAppLib.UITestAccounts(logger)
    ap.Open() # first, open the accounts dialog window
    ap.CreateAccount("WebDAV")
    ap.TypeValue("displayName", uw("Publish Test WebDAV"))
    ap.TypeValue("host", "qacosmo.osafoundation.org")
    ap.TypeValue("path", "cosmo/home/demo1")
    ap.TypeValue("username", "demo1")
    ap.TypeValue("password", "ad3leib5")
    ap.TypeValue("port", "8080")
    ap.ToggleValue("ssl", False)
    ap.ToggleValue("default", True)
    ap.Ok()

    # verification
    ap.VerifyValues("WebDAV", uw("Publish Test WebDAV"), displayName = uw("Publish Test WebDAV"), host = "qacosmo.osafoundation.org", username = "demo1", password="ad3leib5", port=8080)

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
        
        app = wx.GetApp()
        
        # We are interested in seeing how quickly we can upload the collection
        logger.Start('Publish')
        win.PublishCollection()
        while not win.done:
            app.Yield()
        logger.Stop()

        if not win.success:        
            logger.ReportFailure("(On publish collection)")
        
        # Get a read-write ticket to the published collection
        # XXX This is ripped from PublishCollection
        if win.publishType == 'freebusy':
            share = sharing.getFreeBusyShare(win.collection)
        else:
            share = sharing.getShare(win.collection)
        urls = sharing.getUrls(share)
        if len(urls) == 1:
            urlString = urls[0]
        elif win.publishType == 'freebusy':
            urlString = urls[1]
        else:
            urlString = urls[0] # read-write
        
        #Done button call
        win.OnPublishDone(None)
        app.Yield()

        # Unsubscribe and delete the (local) collection we just published so
        # that we can subscribe to it below.
        sharing.unsubscribe(collection)
        collection.delete(recursive=True)
        User.idle()

        # Subscribe to the remote collection
        win = SubscribeCollection.Show(wx.GetApp().mainFrame,
            view=App_ns.itsView, modal=False)
        url = win.toolPanel.GetChildren()[1]
        url.SetFocus()
        url.Clear()
        
        QAUITestAppLib.scripting.User.emulate_typing(urlString)
    
        # We are interested in seeing how quickly we can download the collection
        logger.Start('Subscribe')
        win.OnSubscribe(None)
        while win.subscribing:
            app.Yield()
        logger.Stop()
        
        User.idle()
    
        # verification
        if QAUITestAppLib.scripting.User.emulate_sidebarClick(App_ns.sidebar, "testSharing"):
            # cleanup
            # cosmo can only handle so many shared calendars
            # so remove this one when done
            unpublish(sidebarCollectionNamed('testSharing'))

            logger.ReportPass("(On Subscribe collection)")
        else:
            logger.ReportFailure("(On Subscribe collection)")
        
        logger.SetChecked(True)
finally:
    # cleaning
    logger.Report('Sharing')
    logger.Close()

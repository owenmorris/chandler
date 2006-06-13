import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import flickr
import application.Globals as Globals
import socket

class TestFlickr(ChandlerTestCase):
    
    def startTest(self):
            
        # switch to the all view
        testView = QAUITestAppLib.UITestView(self.logger)
    
        # We need to look at the all view
        testView.SwitchToAllView()
    
        # can't do the next two steps because modal dialogs don't work
        # with emulate_typing
    #    app_ns().root.NewFlickrCollectionByTag()
    #    User.emulate_typing("oscon2005")
    
        # this is what we do instead
        repView = self.app_ns.itsView
        cpiaView = Globals.views[0]
        # get a collection of photos from the oscon2005 tag
        fc = flickr.PhotoCollection(itsView = repView)
        fc.tag = flickr.Tag.getTag(repView, "oscon2005")
        fc.displayName = "oscon2005"
    
        self.logger.startAction('Get a flickr collection by tag')
        try:
            fc.fillCollectionFromFlickr(repView)
        except socket.timeout:
            self.logger.endAction(True, "Flickr timed out; skipping test")
        else:
    
            # Add the channel to the sidebar
            self.app_ns.sidebarCollection.add(fc)
    
            def sidebarCollectionNamed(name):
                """
                Look for a sidebar collection with name, otherwise return False
                """
                sidebarWidget = self.app_ns.sidebar.widget
                for i in range(sidebarWidget.GetNumberRows()):
                    collection = sidebarWidget.GetTable().GetValue(i,0)[0]
                    if collection.displayName == name:
                        return collection
                return False
    
            # force sidebar to update
            self.scripting.User.idle()
    
            # check results
            col = sidebarCollectionNamed("oscon2005")
            if not col:
                self.logger.endAction(False, "Flickr Collection wasn't created")
            if col and len(col) != 10:
                self.logger.endAction(False, "Flickr Collection had the wrong number of elements: %d, expected %d" % (len(col.item), 10))
            self.logger.endAction(True, "Flickr collection of correct size created")


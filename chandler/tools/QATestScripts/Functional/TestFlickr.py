import tools.QAUITestAppLib as QAUITestAppLib
import flickr
import application.Globals as Globals

# initialization
fileName = "TestFlickr.log"
logger = QAUITestAppLib.QALogger(fileName, "TestFlickr")

try:
    logger.Start("Flickr parcel")

    # switch to the all view
    testView = QAUITestAppLib.UITestView(logger)

    # We need to look at the all view
    testView.SwitchToAllView()

    # can't do the next two steps because modal dialogs don't work
    # with emulate_typing
#    app_ns().root.NewFlickrCollectionByTag()
#    User.emulate_typing("oscon2005")

    # this is what we do instead
    repView = app_ns().itsView
    cpiaView = Globals.views[0]
    # get a collection of photos from the oscon2005 tag
    fc = flickr.PhotoCollection(itsView = repView)
    fc.tag = flickr.Tag.getTag(repView, "oscon2005")
    fc.displayName = "oscon2005"
    fc.fillCollectionFromFlickr(repView)

    # Add the channel to the sidebar
    app_ns().sidebarCollection.add(fc)

    def sidebarCollectionNamed(name):
        """
        Look for a sidebar collection with name, otherwise return False
        """
        sidebarWidget = app_ns().sidebar.widget
        for i in range(sidebarWidget.GetNumberRows()):
            collection = sidebarWidget.GetTable().GetValue(i,0)[0]
            if collection.displayName == "oscon2005":
                return collection
        return False

    # force sidebar to update
    User.idle()

    # check results
    col = sidebarCollectionNamed("oscon2005")
    if not col:
        logger.ReportFailure("Flickr Collection wasn't created")
    if col and len(col) != 10:
        logger.ReportFailure("Flickr Collection had the wrong number of elements: %d, expected %d" % (len(col.item), 10))
    logger.ReportPass("Flickr collection of correct size created")

finally:
    logger.Close()


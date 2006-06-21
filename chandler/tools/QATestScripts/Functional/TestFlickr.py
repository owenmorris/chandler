#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import tools.QAUITestAppLib as QAUITestAppLib
import flickr
import socket
from i18n.tests import uw

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
    # get a collection of photos from the oscon2005 tag
    fc = flickr.PhotoCollection(itsView = repView)
    fc.tag = flickr.Tag.getTag(repView, "oscon2005")
    fc.displayName = uw("oscon2005")

    try:
        fc.fillCollectionFromFlickr(repView)
    except socket.timeout:
        logger.ReportPass("Flickr timed out; skipping test")
    except flickr.flickr.FlickrNotFoundError:
        logger.ReportPass("Flickr search returned nothing; skipping test")        
    else:

        # Add the channel to the sidebar
        app_ns().sidebarCollection.add(fc)

        def sidebarCollectionNamed(name):
            """
            Look for a sidebar collection with name, otherwise return False
            """
            sidebarWidget = app_ns().sidebar.widget
            for i in range(sidebarWidget.GetNumberRows()):
                collection = sidebarWidget.GetTable().GetValue(i,0)[0]
                if collection.displayName == name:
                    return collection
            return False

        # force sidebar to update
        User.idle()

        # check results
        col = sidebarCollectionNamed(uw("oscon2005"))
        if not col:
            logger.ReportFailure("Flickr Collection wasn't created")
        if col and len(col) != 10:
            logger.ReportFailure("Flickr Collection had the wrong number of elements: %d, expected %d" % (len(col.item), 10))
        logger.ReportPass("Flickr collection of correct size created")

finally:
    logger.Close()


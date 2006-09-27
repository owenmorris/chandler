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

import tools.cats.framework.ChandlerTestLib as QAUITestAppLib
from tools.cats.framework.ChandlerTestCase import ChandlerTestCase
import flickr
import socket
from i18n.tests import uw

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
        # get a collection of photos from the oscon2005 tag
        fc = flickr.PhotoCollection(itsView = repView)
        fc.tag = flickr.Tag.getTag(repView, "oscon2005")
        fc.displayName = uw("oscon2005")
    
        self.logger.startAction('Get a flickr collection by tag')
        try:
            fc.fillCollectionFromFlickr(repView)
        except socket.timeout:
            self.logger.endAction(True, "Flickr timed out; skipping test")
        except IOError, e:
            self.logger.endAction(True, "IOError (%s); skipping test" % str(e))
        except flickr.flickr.FlickrNotFoundError:
            self.logger.endAction(True, "Flickr search returned nothing; skipping test")
        except flickr.flickr.FlickrError, e:
            self.logger.endAction(True, "Flickr service error (%s); skipping test" % str(e))
        else:
    
            # Add the channel to the sidebar
            self.app_ns.sidebarCollection.add(fc)
    
            # force sidebar to update
            self.scripting.User.idle()
    
            # check results
            col = QAUITestAppLib.sidebarCollectionNamed(uw("oscon2005"))
            if not col:
                self.logger.endAction(False, "Flickr Collection wasn't created")
            if col and len(col) != 10:
                self.logger.endAction(False, "Flickr Collection had the wrong number of elements: %d, expected %d" % (len(col.item), 10))
            self.logger.endAction(True, "Flickr collection of correct size created")


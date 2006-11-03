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
import wx

class TestCertstoreView(ChandlerTestCase):
    
    def startTest(self):
    
        # Make sure we start with the calendar view
        self.app_ns.appbar.press(name="ApplicationBarEventButton")
        wx.GetApp().Yield()
            
        # 1. Add certstore to sidebar
        self.app_ns.root.addCertificateToSidebarEvent()
    
        # force sidebar to update
        self.scripting.User.idle()
        
        # confirm that exactly one entry in the sidebar exists
        def exactlyOneSidebarCollectionNamed(name):
            """
            Look for a sidebar collection with name, otherwise return False
            """
            self.logger.startAction("Checking that we have exactly one collection named %s" % name)
            entries = []
            sidebarWidget = self.app_ns.sidebar.widget
            for i in range(sidebarWidget.GetNumberRows()):
                collection = sidebarWidget.GetTable().GetValue(i,0)[0]
                if collection.displayName == name:
                    entries.append(collection)
            lenEntries = len(entries)
            if lenEntries != 1:
                self.logger.endAction(False, "%s in sidebar %d times, expected 1" % (name, lenEntries))
            else:
                self.logger.endAction(True)
    
        exactlyOneSidebarCollectionNamed("Certificate Store")
    
        # 2. confirm that the view is the All view
        self.logger.startAction("Check view is All")
        if not self.app_ns.appbar.pressed(name='ApplicationBarAllButton'):
            self.logger.endAction(False, "Did not switch to All view as expected")
        else:
            self.logger.endAction(True)
            
        # 3. confirm that the first certificate in the summary view is selected
        self.logger.startAction("Check first certificate selected")
        if self.app_ns.summary.contents.getFirstSelectedItem().displayName != 'Verisign/RSA Secure Server CA':
            self.logger.endAction(False, "RSA certificate not first selected certificate in summary list")
        else:
            self.logger.endAction(True)
    
        # Get a reference to the detail view that we'll use in later tests
        cert = QAUITestAppLib.UITestItem("Certificate", self.logger)
        # Since UITestItem does not know about certificate, we need to set
        # the variables ourselves
        cert.logger = self.logger
        cert.allDay = cert.recurring = False
        cert.view = self.app_ns.itsView
        cert.item = self.app_ns.summary.contents.getFirstSelectedItem() # Dunno how to get it from detail
        
        # Check_DetailView has hardcoded values so we can't use it :(
        cert.CheckEditableBlock('TypeAttribute', 'type', 'root')
        cert.CheckEditableBlock('TrustAttribute', 'trust', '3')
        cert.CheckEditableBlock('FingerprintLabel', 'fingerprint', '0x4463C531D7CCC1006794612BB656D3BF8257846FL')
        cert.CheckEditableBlock('FingerprintAlgLabel', 'algorithm', 'sha1')
        cert.CheckEditableBlock('AsTextAttribute', 'certificate', """Certificate:
    Data:
        Version: 1 (0x0)
        Serial Number:
            02:ad:66:7e:4e:45:fe:5e:57:6f:3c:98:19:5e:dd:c0
        Signature Algorithm: md2WithRSAEncryption
        Issuer: C=US, O=RSA Data Security, Inc., OU=Secure Server Certification Authority
        Validity
            Not Before: Nov  9 00:00:00 1994 GMT
            Not After : Jan  7 23:59:59 2010 GMT
        Subject: C=US, O=RSA Data Security, Inc., OU=Secure Server Certification Authority
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
            RSA Public Key: (1000 bit)
                Modulus (1000 bit):
                    00:92:ce:7a:c1:ae:83:3e:5a:aa:89:83:57:ac:25:
                    01:76:0c:ad:ae:8e:2c:37:ce:eb:35:78:64:54:03:
                    e5:84:40:51:c9:bf:8f:08:e2:8a:82:08:d2:16:86:
                    37:55:e9:b1:21:02:ad:76:68:81:9a:05:a2:4b:c9:
                    4b:25:66:22:56:6c:88:07:8f:f7:81:59:6d:84:07:
                    65:70:13:71:76:3e:9b:77:4c:e3:50:89:56:98:48:
                    b9:1d:a7:29:1a:13:2e:4a:11:59:9c:1e:15:d5:49:
                    54:2c:73:3a:69:82:b1:97:39:9c:6d:70:67:48:e5:
                    dd:2d:d6:c8:1e:7b
                Exponent: 65537 (0x10001)
    Signature Algorithm: md2WithRSAEncryption
        65:dd:7e:e1:b2:ec:b0:e2:3a:e0:ec:71:46:9a:19:11:b8:d3:
        c7:a0:b4:03:40:26:02:3e:09:9c:e1:12:b3:d1:5a:f6:37:a5:
        b7:61:03:b6:5b:16:69:3b:c6:44:08:0c:88:53:0c:6b:97:49:
        c7:3e:35:dc:6c:b9:bb:aa:df:5c:bb:3a:2f:93:60:b6:a9:4b:
        4d:f2:20:f7:cd:5f:7f:64:7b:8e:dc:00:5c:d7:fa:77:ca:39:
        16:59:6f:0e:ea:d3:b5:83:7f:4d:4d:42:56:76:b4:c9:5f:04:
        f8:38:f8:eb:d2:5f:75:5f:cd:7b:fc:e5:8e:80:7c:fc:50
""")
        
        # 5. Change certificate trust
        # SetAttr has hardcode values :(
        cert.SetEditableBlock('TrustAttribute', 'trust', '0', False)
        self.scripting.User.idle()
        cert.CheckEditableBlock('TrustAttribute', 'trust', '0')
    
        # Switch back to calendar view
        self.app_ns.appbar.press(name="ApplicationBarEventButton")
        wx.GetApp().Yield()        
        # Add certstore to sidebar again
        self.app_ns.root.addCertificateToSidebarEvent()
        # force sidebar to update
        self.scripting.User.idle()
        # 6. Check that we still have just one certificate store in the sidebar
        exactlyOneSidebarCollectionNamed("Certificate Store")
    
        # 7. Check that we still have the same first cert and the changed value
        # was persisted
        cert.CheckEditableBlock('FingerprintLabel', 'fingerprint', '0x4463C531D7CCC1006794612BB656D3BF8257846FL')
        cert.CheckEditableBlock('TrustAttribute', 'trust', '0')
        
        # Switch to calendar view
        self.app_ns.appbar.press(name="ApplicationBarEventButton")
        wx.GetApp().Yield()        
        # XXX 8. import certificate
        # confirm that we switched to all view, and the newly added cert is
        # selected in summary view and displayed correctly in detail view

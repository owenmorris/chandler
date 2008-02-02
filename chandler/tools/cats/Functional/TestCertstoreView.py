#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
from osaf.framework.certstore import constants

class TestCertstoreView(ChandlerTestCase):
    
    def startTest(self):
    
        # Make sure we start with the calendar view
        self.app_ns.appbar.press("ApplicationBarEventButton")
        application = wx.GetApp()
        application.Yield(True)
            
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
            sidebar = self.app_ns.sidebar
            for i, collection in enumerate(sidebar.contents):
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
        if not self.app_ns.appbar.pressed('ApplicationBarAllButton'):
            self.logger.endAction(False, "Did not switch to All view as expected")
        else:
            self.logger.endAction(True)
            
        # 3. confirm that the first certificate in the summary view is selected
        self.logger.startAction("Check first certificate selected")
        if self.app_ns.summary.contents.getFirstSelectedItem().displayName != 'Go Daddy Class 2 CA':
            self.logger.endAction(False, "Go Daddy certificate not first selected certificate in summary list")
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
        cert.CheckEditableBlock('PurposeAttribute', 'purpose', '%s' % (constants.PURPOSE_CA | constants.PURPOSE_SERVER))
        cert.CheckEditableBlock('TrustAttribute', 'trust', '%s' % (constants.TRUST_AUTHENTICITY | constants.TRUST_SERVER))
        cert.CheckEditableBlock('FingerprintLabel', 'fingerprint', '0x2796bae63f1801e277261ba0d77770028f20eee4L')
        cert.CheckEditableBlock('FingerprintAlgLabel', 'algorithm', 'sha1')
        cert.CheckEditableBlock('AsTextAttribute', 'certificate', """Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 0 (0x0)
        Signature Algorithm: sha1WithRSAEncryption
        Issuer: C=US, O=The Go Daddy Group, Inc., OU=Go Daddy Class 2 Certification Authority
        Validity
            Not Before: Jun 29 17:06:20 2004 GMT
            Not After : Jun 29 17:06:20 2034 GMT
        Subject: C=US, O=The Go Daddy Group, Inc., OU=Go Daddy Class 2 Certification Authority
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
            RSA Public Key: (2048 bit)
                Modulus (2048 bit):
                    00:de:9d:d7:ea:57:18:49:a1:5b:eb:d7:5f:48:86:
                    ea:be:dd:ff:e4:ef:67:1c:f4:65:68:b3:57:71:a0:
                    5e:77:bb:ed:9b:49:e9:70:80:3d:56:18:63:08:6f:
                    da:f2:cc:d0:3f:7f:02:54:22:54:10:d8:b2:81:d4:
                    c0:75:3d:4b:7f:c7:77:c3:3e:78:ab:1a:03:b5:20:
                    6b:2f:6a:2b:b1:c5:88:7e:c4:bb:1e:b0:c1:d8:45:
                    27:6f:aa:37:58:f7:87:26:d7:d8:2d:f6:a9:17:b7:
                    1f:72:36:4e:a6:17:3f:65:98:92:db:2a:6e:5d:a2:
                    fe:88:e0:0b:de:7f:e5:8d:15:e1:eb:cb:3a:d5:e2:
                    12:a2:13:2d:d8:8e:af:5f:12:3d:a0:08:05:08:b6:
                    5c:a5:65:38:04:45:99:1e:a3:60:60:74:c5:41:a5:
                    72:62:1b:62:c5:1f:6f:5f:1a:42:be:02:51:65:a8:
                    ae:23:18:6a:fc:78:03:a9:4d:7f:80:c3:fa:ab:5a:
                    fc:a1:40:a4:ca:19:16:fe:b2:c8:ef:5e:73:0d:ee:
                    77:bd:9a:f6:79:98:bc:b1:07:67:a2:15:0d:dd:a0:
                    58:c6:44:7b:0a:3e:62:28:5f:ba:41:07:53:58:cf:
                    11:7e:38:74:c5:f8:ff:b5:69:90:8f:84:74:ea:97:
                    1b:af
                Exponent: 3 (0x3)
        X509v3 extensions:
            X509v3 Subject Key Identifier: 
                D2:C4:B0:D2:91:D4:4C:11:71:B3:61:CB:3D:A1:FE:DD:A8:6A:D4:E3
            X509v3 Authority Key Identifier: 
                keyid:D2:C4:B0:D2:91:D4:4C:11:71:B3:61:CB:3D:A1:FE:DD:A8:6A:D4:E3
                DirName:/C=US/O=The Go Daddy Group, Inc./OU=Go Daddy Class 2 Certification Authority
                serial:00

            X509v3 Basic Constraints: 
                CA:TRUE
    Signature Algorithm: sha1WithRSAEncryption
        32:4b:f3:b2:ca:3e:91:fc:12:c6:a1:07:8c:8e:77:a0:33:06:
        14:5c:90:1e:18:f7:08:a6:3d:0a:19:f9:87:80:11:6e:69:e4:
        96:17:30:ff:34:91:63:72:38:ee:cc:1c:01:a3:1d:94:28:a4:
        31:f6:7a:c4:54:d7:f6:e5:31:58:03:a2:cc:ce:62:db:94:45:
        73:b5:bf:45:c9:24:b5:d5:82:02:ad:23:79:69:8d:b8:b6:4d:
        ce:cf:4c:ca:33:23:e8:1c:88:aa:9d:8b:41:6e:16:c9:20:e5:
        89:9e:cd:3b:da:70:f7:7e:99:26:20:14:54:25:ab:6e:73:85:
        e6:9b:21:9d:0a:6c:82:0e:a8:f8:c2:0c:fa:10:1e:6c:96:ef:
        87:0d:c4:0f:61:8b:ad:ee:83:2b:95:f8:8e:92:84:72:39:eb:
        20:ea:83:ed:83:cd:97:6e:08:bc:eb:4e:26:b6:73:2b:e4:d3:
        f6:4c:fe:26:71:e2:61:11:74:4a:ff:57:1a:87:0f:75:48:2e:
        cf:51:69:17:a0:02:12:61:95:d5:d1:40:b2:10:4c:ee:c4:ac:
        10:43:a6:a5:9e:0a:d5:95:62:9a:0d:cf:88:82:c5:32:0c:e4:
        2b:9f:45:e6:0d:9f:28:9c:b1:b9:2a:5a:57:ad:37:0f:af:1d:
        7f:db:bd:9f
""")
        
        # 5. Change certificate trust
        # SetAttr has hardcode values :(
        cert.SetEditableBlock('TrustAttribute', 'trust', '0', False)
        self.scripting.User.idle()
        cert.CheckEditableBlock('TrustAttribute', 'trust', '0')
    
        # Switch back to calendar view
        self.app_ns.appbar.press("ApplicationBarEventButton")
        application.Yield(True)   
        # Add certstore to sidebar again
        self.app_ns.root.addCertificateToSidebarEvent()
        # force sidebar to update
        self.scripting.User.idle()
        # 6. Check that we still have just one certificate store in the sidebar
        exactlyOneSidebarCollectionNamed("Certificate Store")
    
        # 7. Check that we still have the same first cert and the changed value
        # was persisted
        cert.CheckEditableBlock('FingerprintLabel', 'fingerprint', '0x2796bae63f1801e277261ba0d77770028f20eee4L')
        cert.CheckEditableBlock('TrustAttribute', 'trust', '0')
        
        # Switch to calendar view
        self.app_ns.appbar.press("ApplicationBarEventButton")
        application.Yield(True)     
        # XXX 8. import certificate
        # confirm that we switched to all view, and the newly added cert is
        # selected in summary view and displayed correctly in detail view

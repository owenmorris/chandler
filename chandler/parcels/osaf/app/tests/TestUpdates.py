#   Copyright (c) 2008 Open Source Applications Foundation
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

import osaf.app.updates as updates
import xml.etree.ElementTree as ElementTree
import PyICU
import unittest

class ParseTestCase(unittest.TestCase):

    def testInvalidXML(self):
        self.failUnlessRaises(SyntaxError, lambda: list(updates.iterVersions("woot")))
    
    def testNoReleases(self):
        self.failUnlessEqual(list(updates.iterVersions("<x><y /></x>")), [])

    def testNoReleaseVersion(self):
        result = list(updates.iterVersions(
"""<a><b class="release-info">
<x href="http://www.example.com/" class="announcement-url" />
</b></a>"""
        ))
        self.failUnlessEqual(result, [])

    def testReleaseVersionOnly(self):
        result = list(updates.iterVersions(
"""<a><b class="release-info">
<c class="release-version">1.0.blurdy</c>
<x href="http://www.example.com/" class="announcement-url" />
</b></a>"""
        ))
        self.failUnlessEqual(
            result,
            [("1.0.blurdy", {}, "http://www.example.com/", None)]
        )

    def testSingleReleaseNoFeatureAnnounce(self):
        result = list(updates.iterVersions(
"""<a><b class="release-info">
<c class="release-version">1.0.blurdy</c>
<x href="http://www.example.com/" class="announcement-url" />
<woot href="http://www.example.com/download.zip" class="download-the-bestest">Woot!</woot>
</b></a>"""
        ))
        self.failUnlessEqual(
            result, [
                ("1.0.blurdy",
                { "the-bestest": "http://www.example.com/download.zip"},
                "http://www.example.com/",
                None)
            ]
        )

    def testSingleRelease(self):
        result = list(updates.iterVersions(
"""<a><b class="release-info">
<c class="release-version">1.0.blurdy</c>
<x href="http://www.example.com/" class="announcement-url" />
<woot href="http://www.example.com/download.zip" class="download-the-bestest">Woot!</woot>
<aha class="release-new-features">Now with vim &amp; verve</aha>
</b></a>"""
        ))
        self.failUnlessEqual(
            result, [
                ("1.0.blurdy",
                { "the-bestest": "http://www.example.com/download.zip"},
                "http://www.example.com/",
                "Now with vim & verve")
            ]
        )

    def testMultipleLangs(self):
        save_locale = PyICU.Locale.getDefault()
        
        PyICU.Locale.setDefault(PyICU.Locale.createFromName('fr_FR'))
        
        try:
            result = list(updates.iterVersions(
    """<a><b class="release-info">
    <c class="release-version">1.0.blurdy</c>
    <x href="http://www.example.com/" class="announcement-url" />
    <woot href="http://www.example.com/download.zip" class="download-the-bestest">Woot!</woot>
    <aha class="release-new-features">Now with vim &amp; verve</aha>
    <x class="release-new-features" lang="fr">Bonjour, mesdames et messieurs</x>
    </b></a>"""
            ))
            self.failUnlessEqual(
                result, [
                    ("1.0.blurdy",
                    { "the-bestest": "http://www.example.com/download.zip"},
                    "http://www.example.com/",
                    "Bonjour, mesdames et messieurs")
                ]
            )
        finally:
            if save_locale is not None:
                PyICU.Locale.setDefault(save_locale)

    def testDefaultLang(self):
        save_locale = PyICU.Locale.getDefault()
        
        PyICU.Locale.setDefault(PyICU.Locale.createFromName('en_US'))
        
        try:
            result = list(updates.iterVersions(
    """<a><b class="release-info">
    <c class="release-version">1.0.blurdy</c>
    <x href="http://www.example.com/" class="announcement-url" />
    <woot href="http://www.example.com/download.zip" class="download-the-bestest">Woot!</woot>
    <aha class="release-new-features">Now with vim &amp; verve</aha>
    <x class="release-new-features" lang="fr">Bonjour, mesdames et messieurs</x>
    <x class="release-new-features" lang="de">Guten tag, alle</x>
    </b></a>"""
            ))
            self.failUnlessEqual(
                result, [
                    ("1.0.blurdy",
                    { "the-bestest": "http://www.example.com/download.zip"},
                    "http://www.example.com/",
                    "Now with vim & verve")
                ]
            )
        finally:
            if save_locale is not None:
                PyICU.Locale.setDefault(save_locale)

    def testFallbackWithNoDefault(self):
        save_locale = PyICU.Locale.getDefault()
        
        PyICU.Locale.setDefault(PyICU.Locale.createFromName('zh_CN'))
        
        try:
            result = list(updates.iterVersions(
    """<a><b class="release-info">
    <c class="release-version">1.0.blurdy</c>
    <x href="http://www.example.com/" class="announcement-url" />
    <woot href="http://www.example.com/download.zip" class="download-the-bestest">Woot!</woot>
    <x class="release-new-features" lang="fr">Bonjour, mesdames et messieurs</x>
    <x class="release-new-features" lang="de">Guten tag, alle</x>
    <x class="release-new-features" lang="en">Here we go?</x>
    </b></a>"""
            ))
            self.failUnlessEqual(
                result, [
                    ("1.0.blurdy",
                    { "the-bestest": "http://www.example.com/download.zip"},
                    "http://www.example.com/",
                    "Bonjour, mesdames et messieurs")
                ]
            )
        finally:
            if save_locale is not None:
                PyICU.Locale.setDefault(save_locale)

    def testCurrent(self):
        result = list(updates.iterVersions(
"""<div class="release-info" id="chandler-0.7.5.1">
<h1>Download Chandler Desktop <span class="release-version">0.7.5.1</span></h1>
<p />
<h2><a href="http://downloads.osafoundation.org/chandler/releases/0.7.5.1/Chandler_win_0.7.5.1.exe" target="_top" class="download-windows">Windows</a> |
<a href="http://downloads.osafoundation.org/chandler/releases/0.7.5.1/#enduserlinux" target="_top">Linux</a> |
Mac OS X:
<a href="http://downloads.osafoundation.org/chandler/releases/0.7.5.1/Chandler_ppc-osx_0.7.5.1.dmg" target="_top" class="download-osx-ppc">PPC</a> |
<a href="http://downloads.osafoundation.org/chandler/releases/0.7.5.1/Chandler_intel-osx_0.7.5.1.dmg" target="_top" class="download-osx-intel">Intel</a> | <a href="http://downloads.osafoundation.org/chandler/releases/0.7.5.1/Chandler_intel-osx-leopard_0.7.5.1.dmg" target="_top" class="download-osx-intel-10.5">Leopard</a> </h2>
<a href="http://downloads.osafoundation.org/chandler/releases/0.7.5.1/Chandler_linux_0.7.5.1-1_i386.deb" class="download-linux" style="display:none"></a>
<p />
<div style="display:none">
<div class="release-new-features" lang="en">Drag-and-droppable sidebar collections</div>
</div>
<h3><a href="http://blog.chandlerproject.org/2008/03/26/chandler-0751/" class="announcement-url">Release announcement and notes for 0.7.5.1</a> </h3>
</div>
"""))
        self.failUnlessEqual(len(result), 1)
        
        t = result[0]
        self.failUnlessEqual(t[0], '0.7.5.1')
        self.failUnlessEqual(t[2], 'http://blog.chandlerproject.org/2008/03/26/chandler-0751/')
        self.failUnlessEqual(t[1], {
                'linux': 'http://downloads.osafoundation.org/chandler/releases/0.7.5.1/Chandler_linux_0.7.5.1-1_i386.deb',
                'osx-ppc': 'http://downloads.osafoundation.org/chandler/releases/0.7.5.1/Chandler_ppc-osx_0.7.5.1.dmg',
                'osx-intel-10.5': 'http://downloads.osafoundation.org/chandler/releases/0.7.5.1/Chandler_intel-osx-leopard_0.7.5.1.dmg',
                'osx-intel': 'http://downloads.osafoundation.org/chandler/releases/0.7.5.1/Chandler_intel-osx_0.7.5.1.dmg',
                'windows': 'http://downloads.osafoundation.org/chandler/releases/0.7.5.1/Chandler_win_0.7.5.1.exe',
            }
        )
        self.failUnlessEqual(t[3], "Drag-and-droppable sidebar collections")

class MatchPlatformTestCase(unittest.TestCase):

    TEST_DICT = {
        'linux' : '<generic linux url>',
        'windows' : '<generic windows url>',
        'osx-ppc' : '<mac ppc url>',
        'os-intel' : '<mac intel url>',
        'osx-intel-10.5' : '<mac Leopard intel url>',
    }

    def testNoValue(self):
        self.failUnless(updates.matchDownloadUrl({}) is None)
    
    def testLinux(self):
        self.failUnlessEqual(
            updates.matchDownloadUrl(self.TEST_DICT, 'linux',
                                     'Ubuntu-6.06-dapper'),
            '<generic linux url>'
        )

    def testWindows(self):
        self.failUnlessEqual(
            updates.matchDownloadUrl(self.TEST_DICT, 'win', '5.1-WinNT'),
            '<generic windows url>'
        )

    def testPPCMacTiger(self):
        self.failUnlessEqual(
            updates.matchDownloadUrl(self.TEST_DICT, 'osx-ppc', '10.4-Tiger'),
            '<mac ppc url>'
        )

    def testPPCMacLeopard(self):
        self.failUnlessEqual(
            updates.matchDownloadUrl(self.TEST_DICT, 'osx-ppc', '10.5-Leopard'),
            '<mac ppc url>'
        )

    def testIntelMacTiger(self):
        self.failUnlessEqual(
            updates.matchDownloadUrl(self.TEST_DICT, 'osx-intel', '10.4-Tiger'),
            '<mac intel url>'
        )

    def testIntelMacTiger(self):
        self.failUnlessEqual(
            updates.matchDownloadUrl(self.TEST_DICT, 'osx-intel', '10.5-Leopard'),
            '<mac Leopard intel url>'
        )


if __name__ == "__main__":
    unittest.main()


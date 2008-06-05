from application import schema, Utility
import osaf.startup as startup
import osaf.sharing as sharing
from osaf.framework.blocks.Styles import getFont
import datetime
import xml.etree.cElementTree as ElementTree
import pkg_resources
import version
import wx
import logging
import PyICU
from i18n import ChandlerMessageFactory as _

logger = logging.getLogger(__name__)

class UpdateDialog(wx.Dialog):

    def __init__(self, release, download, announcement, feature=None):
        parent = getattr(wx.GetApp(), 'mainFrame', None)
        super(UpdateDialog, self).__init__(
            parent, -1, title=_(u"Upgrade"),
            size=wx.DefaultSize, pos=wx.DefaultPosition,
            style=wx.DEFAULT_DIALOG_STYLE
        )
        self.download = download
        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        logo = wx.GetApp().GetImage("Chandler_128.png")
        bitmap = wx.StaticBitmap(self, -1, logo)
        self.Sizer.Add(bitmap, 0, wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, 15)
        
        msg = _(u"A new version of Chandler has been released: %(version)s") % {
                 'version' : release }

        message = wx.StaticText(self, -1, msg)
        message.Font = getFont(size=15.0)
        self.Sizer.Add(message, 0, wx.GROW|wx.ALL, 15.0)
        
        if feature:
            featureSizer = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(self, -1, _(u"NEW FEATURE"))
            label.Font = getFont(size=10.0, weight=wx.FONTWEIGHT_BOLD)

            featureSizer.AddSpacer((15, 0))
            featureSizer.Add(label, 0, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.TOP, 1)
            
            featureText = wx.StaticText(self, -1, feature)
            featureText.Font = getFont(size=12.0)
            featureText.Wrap(300)
            featureSizer.Add(featureText, 0, wx.GROW|wx.LEFT|wx.ALIGN_TOP, 5)
            self.Sizer.Add(featureSizer, 0, wx.GROW|wx.BOTTOM, 30)
            
        buttonSizer = wx.StdDialogButtonSizer()
        if announcement is not None:
            hyper = wx.HyperlinkCtrl(self, -1,
                        _(u"See what's new."),
                        announcement.decode('UTF-8'),
                        style=wx.ALIGN_LEFT)
            hyper.SetNormalColour("#0080ff")
            hyper.SetVisitedColour("#0080ff")
            hyper.SetHoverColour("#9999cc")
            hyper.Font = getFont(size=12.0)

            buttonSizer.Add(hyper, 0, wx.GROW|wx.ALIGN_LEFT|wx.LEFT, 15)
            
        default = wx.Button(self, wx.ID_OK, u"Upgrade")
        buttonSizer.AddButton(default)
        buttonSizer.AddButton(wx.Button(self, wx.ID_CANCEL, _(u"Later")))
        default.SetDefault()
        buttonSizer.Realize()
        
        self.Sizer.Add(buttonSizer, 0, wx.GROW|wx.BOTTOM, 12)

        self.SetAutoLayout(True)
        self.Sizer.Fit(self)

        if parent: self.CenterOnParent()

    def ShowModal(self):
        result = super(UpdateDialog, self).ShowModal()
        
        if result == wx.ID_OK:
            wx.LaunchDefaultBrowser(self.download, wx.BROWSER_NEW_WINDOW)
            self.Hide()
            wx.GetApp().shutdown(forceBackup=True)

def parseRelease(xmlElement):
    release = None
    urls = {}
    announcement = None
    langsAndFeatures = []
    feature = None
    featureLang = None
    
    for elt in xmlElement.getiterator():
        cls = elt.get('class')
        href = elt.get('href')
        
        if cls == 'release-version':
            release = elt.text
        elif cls == 'release-new-features':
            langsAndFeatures.append((elt.get('lang'), elt.text))
        elif href:
            if cls == 'announcement-url':
                announcement = href
            elif cls and cls.startswith('download-'):
                urls[cls[len('download-'):]] = href

    defaultLocale = PyICU.Locale.getDefault()
    
    if defaultLocale is None:
        defaultLocale = PyICU.Locale.getUS()

    defaultLang = defaultLocale.getLanguage()

    for xmlLang, xmlFeature in langsAndFeatures:
        if defaultLang == xmlLang:
            featureLang, feature = xmlLang, xmlFeature
            break
        
        if ( (feature is None) or
             (featureLang is not None and xmlLang is None) ):
            featureLang, feature = xmlLang, xmlFeature
            

    return release, urls, announcement, feature

def matchDownloadUrl(urls, platformID=Utility.getPlatformID(),
                     osName=Utility.getOSName()):

    matchedPlatform = ''
    matchedURL = None

    if platformID in ('win', 'win-cygwin'):
        platformID = 'windows'

    components = ("%s-%s" % (platformID, osName)).split('-')
    
    for platform, url in urls.iteritems():
        theseComponents = platform.split('-')
        if (components[:len(theseComponents)] == theseComponents and
            len(platform) > len(matchedPlatform)):
            
            matchedPlatform = platform
            matchedURL = url

    return matchedURL

def iterVersions(xmlData):
    xml = ElementTree.XML(xmlData)
        
    for elt in xml.getiterator():
       if elt.get('class') == 'release-info':
           t = parseRelease(elt)
           
           if t[0] is not None: yield t

class UpdateCheckTask(startup.DurableTask):
    #TEST_URL = "http://builds.osafoundation.org/chandler/test-chandler.html"
    TEST_URL = "http://localhost/test-chandler.html"
    MAIN_URL = "http://downloads.osafoundation.org/latest-chandler.html"

    stopped = schema.One(schema.Boolean, defaultValue=False)

    def getTarget(self):
        return lambda task: task

    def run(self, inform_user=False, url=MAIN_URL):
        d = sharing.getPage(self.itsView, url)
        
        d.addCallback(
            self._gotData, url, inform_user
        ).addErrback(
            self._failed, url, inform_user
        )
        return True
        
    def stop(self):
        self.stopped = True
        super(UpdateCheckTask, self).stop()

    def reschedule(self, *args, **kw):
        if self.stopped: del self.stopped
        super(UpdateCheckTask, self).reschedule(*args, **kw)

    def _showDialog(self, release, download, announcement, feature):
        dialog = UpdateDialog(release, download, announcement, feature)
        dialog.CenterOnParent()
        dialog.ShowModal()
        dialog.Destroy()

    def _gotData(self, data, url, inform_user):
        current = pkg_resources.parse_version(version.version)
        mostRecentInfo = None
    
        for vInfo in iterVersions(data):
            logger.debug("Found release %s", vInfo[0])
            parsedVersion = pkg_resources.parse_version(vInfo[0])
            download = matchDownloadUrl(vInfo[1])
            
            if download is not None and parsedVersion > current:
                mostRecentInfo = (vInfo[0], download, vInfo[2], vInfo[3])
                current = parsedVersion
        
        if mostRecentInfo is None:
            logger.info("No version newer than '%s' found", version.version)
            if inform_user:
                wx.CallAfter(
                    wx.MessageBox,
                    _(u"Your Chandler (version %(version)s) is up-to-date.") % {
                       'version': version.version
                    },
                    _(u"Update Check"),
                )
        else:
            logger.info("Newer version '%s' found", mostRecentInfo[0])
            wx.CallAfter(self._showDialog, *mostRecentInfo)


    def _failed(self, failure, url, inform_user):
        logger.warning("Failed to get update information: %s", failure)

        if inform_user:
            if failure.check(sharing.errors.SharingError):
                message = failure.value.message
            else:
                message = _(u"Chandler was unable to retrieve information about new updates. See the log file for details.")
        
            wx.CallAfter(wx.MessageBox, message, _(u"Problem Getting Update Info"))

if __name__ == "__main__":
    class TestApp(wx.App):
        def GetImage(self, name):
            from i18n import getImage
            import cStringIO
            
            f = getImage(name)
            
            raw = wx.ImageFromStream(cStringIO.StringIO(f.read())).Copy()
            return wx.BitmapFromImage(raw)

        def OnInit(self):
            dialog = UpdateDialog(
                         "0.9.9", "http://www.chandlerproject.org/download",
                         "http://chandlerproject.org/",
            "Double click in the List View to view and edit items in an independent detail view")
            result = dialog.ShowModal()
            dialog.Destroy()
            return False

    app = TestApp(0)
    app.MainLoop()



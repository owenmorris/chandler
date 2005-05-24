"""
Certificate

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import wx
import application
import osaf.framework.blocks.Block as Block
import application.Globals as Globals
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.ContentModel as ContentModel
import osaf.framework.blocks.detail.Detail as Detail
import M2Crypto.BIO as BIO
import M2Crypto.X509 as X509
import M2Crypto.util as util
import M2Crypto.EVP as EVP

TRUST_AUTHENTICITY = 1
TRUST_SITE         = 2

class Certificate(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/certstore/schema/Certificate"

    def pemAsString(self):
        # M2Crypto needs this to be str rather than unicode - safe conversion
        return str(self.pem.getReader().read())

    def asTextAsString(self):        
        return self.asText.getReader().read()

    def asX509(self):
        return X509.load_cert_string(self.pemAsString())

    # XXX These don't work?
    def getAuthenticityBit(self):
        return bool(self.trust & TRUST_AUTHENTICITY)
    def setAuthenticityBit(self, authBit):
        if authBit:
            self.trust |= TRUST_AUTHENTICITY
        else:
            self.trust &= ~TRUST_AUTHENTICITY
    authenticityBit = property(getAuthenticityBit, setAuthenticityBit,
                               doc='Authenticity bit.')

    def getSiteBit(self):
        return bool(self.trust & TRUST_SITE)
    def setSiteBit(self, siteBit):
        if siteBit:
            self.trust |= TRUST_SITE
        else:
            self.trust &= ~TRUST_SITE
    siteBit = property(getSiteBit, setSiteBit,
                       doc='Site bit.')


class CertificateViewController(Block.Block):
    def onCertificateViewBlockEvent(self, event):
        CreateSidebarView(self.itsView, Globals.views[0])


class CertificateImportController(Block.Block):
    def onCertificateImportBlockEvent(self, event):
        ImportCertificate(self.itsView, Globals.views[0])


def _fingerprint(x509, md='sha1'):
    der = x509.as_der()
    md = EVP.MessageDigest(md)
    md.update(der)
    digest = md.final()
    return hex(util.octx_to_num(digest))


def _importCertificate(x509, fingerprint, trust, repView):
    subjectCommonName = x509.get_subject().CN
    pem = x509.as_pem()
    asText = x509.as_text()

    cert = Certificate(view=repView)
    text = cert.getAttributeAspect('pem', 'type').makeValue(pem,
                                                           compression=None)
    cert.pem = text
    text = cert.getAttributeAspect('asText', 'type').makeValue(asText)
    cert.asText = text
    cert.type = 'root'#XXX check the cert before blindly assigning this
    cert.trust = trust
    cert.fingerprintAlgorithm = 'sha1'
    cert.fingerprint = fingerprint
    cert.subjectCommonName = subjectCommonName
    repView.refresh()


def ImportCertificate(repView, cpiaView):
    dlg = wx.FileDialog(wx.GetApp().mainFrame,
                        "Choose a certificate to import",
                        "", "", "PEM files|*.pem;*.crt|All files (*.*)|*.*",
                        wx.OPEN | wx.HIDE_READONLY)
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
        dlg.Destroy()
        if path == '':
            return
    else:
        dlg.Destroy()
        return
    
    try: 
        x509 = X509.load_cert(path)
        
        fingerprint = _fingerprint(x509)

        # XXX Determine rootness before so we don't show bogus options, and
        # XXX can customize the text.
        dlg = wx.MultiChoiceDialog(wx.GetApp().mainFrame,
                                   "Do you want to import this certificate?\n" +
                                   "Type: root\n" + # XXX determine type
                                   "SHA1 fingerprint: " + fingerprint +
                                   "\n" + x509.as_text(),
                                   "Import check",
                                   choices=["Trust the authenticity of this certificate.",
                                            "Trust this certificate to sign site certificates."])
        trust = 0
        if dlg.ShowModal() == wx.ID_OK:
            selections = dlg.GetSelections()
            dlg.Destroy()
            # XXX Number of selections depends on type of cert
            for sel in selections:
                if sel == 0:
                    trust |= TRUST_AUTHENTICITY
                if sel == 1:
                    trust |= TRUST_SITE
        else:
            dlg.Destroy()
            return

        _importCertificate(x509, fingerprint, trust, repView)
    except:
        application.dialogs.Util.ok(wx.GetApp().mainFrame, "Error", 
            "Could not add certificate from: " + path + 
            "\nCheck the path and try again.")
        return


def CreateSidebarView(repView, cpiaView):
    qString = u'for i in "//parcels/osaf/framework/certstore/schema/Certificate" where True'
    sidebar = ItemCollection.ItemCollection(view=repView)
    sidebar.displayName = 'Certificate Store'
    sidebar._rule = qString

    # XXX Should be done using ref collections instead?
    import repository.query.Query as Query

    qName = 'certificateStoreQuery'
    q = repView.findPath('//Queries/%s' %(qName))
    if q is None:
        p = repView.findPath('//Queries')
        k = repView.findPath('//Schema/Core/Query')
        q = Query.Query(qName, p, k, qString)
    for item in q:
        sidebar.add(item)

    cpiaView.postEventByName('AddToSidebarWithoutCopying',
                             {'items': [sidebar]})


class EditIntegerAttribute (Detail.EditTextAttribute):
    #XXX Get rid of this as soon as boolean editors work with properties
    def saveAttributeFromWidget(self, item, widget, validate):
        if validate:
            item.setAttributeValue(self.whichAttribute(), int(widget.GetValue()))

    def loadAttributeIntoWidget(self, item, widget):
        try:
            value = item.getAttributeValue(self.whichAttribute())
        except AttributeError:
            value = 0
        wiVal = widget.GetValue()
        if not wiVal or int(wiVal) != value:
            widget.SetValue(str(value))


class AsTextAttribute (Detail.EditTextAttribute):
    #XXX Get rid of this, asText should be normal (readonly) value
    def saveAttributeFromWidget(self, item, widget, validate):
        pass

    def loadAttributeIntoWidget(self, item, widget):
        value = item.asTextAsString()
        if widget.GetValue() != value:
            widget.SetValue(value)
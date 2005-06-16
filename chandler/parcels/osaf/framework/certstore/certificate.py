"""
Certificate

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""
__parcel__ = "osaf.framework.certstore.schema"

import wx
import application
import osaf.framework.blocks.Block as Block
import application.Globals as Globals
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.ContentModel as ContentModel
import osaf.framework.blocks.detail.Detail as Detail
import osaf.framework.certstore.notification as notification
import M2Crypto.X509 as X509
import M2Crypto.util as util
import M2Crypto.EVP as EVP

# XXX Should be done using ref collections instead?
import repository.query.Query as Query


TRUST_AUTHENTICITY = 1
TRUST_SITE         = 2

TRUSTED_SITE_CERTS_QUERY_NAME = 'sslTrustedSiteCertificatesQuery'
ALL_CERTS_QUERY = u'for i in "//parcels/osaf/framework/certstore/schema/Certificate" where True'

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


###
# XXX begin store.py

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


def _isSiteCertificate(x509):
    # XXX This will need tweaks
    site = False
    try:
        host = x509.get_ext('subjectAltName').get_value()
        host = host.lower()
        if host[:4] == 'dns:':
            site = True
    except LookupError:
        pass
        
    if not site:
        try:
            commonName = x509.get_subject().CN
            if commonName.find('.') > -1 and commonName.find(' ') < 0:
                site = True
        except AttributeError:
            pass
            
    return site


def _certificateType(x509):
    # Determine certificate type.
    # XXX This will need tweaking, for example
    # XXX X509_check_ca, X509_check_purpose
    type = None
    try:
        if x509.get_ext('basicConstraints').get_value() == 'CA:TRUE':
            type = 'root'
        elif _isSiteCertificate(x509):
            type = 'site'
    except LookupError:
        subject = x509.get_subject()
        issuer = x509.get_issuer()
        if subject.CN == issuer.CN:
            type = 'root'
        elif _isSiteCertificate(x509):
            type = 'site'
                
    if type is None:
        raise Exception, 'could not determine certificate type'
        
    return type

def _allCertificatesQuery(repView):
    qName = 'allCertificatesQuery'
    q = repView.findPath('//Queries/%s' %(qName))
    if q is None:
        p = repView.findPath('//Queries')
        k = repView.findPath('//Schema/Core/Query')
        q = Query.Query(qName, p, k, ALL_CERTS_QUERY)
        notificationItem = repView.findPath('//parcels/osaf/framework/certstore/schema/dummyCertNotification')
        q.subscribe(notificationItem, 'handle', True, True)

    return q

def _isInRepository(repView, pem):
    # XXX This could be optimized by querying based on some cheap field,
    # XXX like subjectCommonName, which would typically return just 0 or 1
    # XXX hit. But I don't want to leave query items laying around either.
    q = _allCertificatesQuery(repView)
    for cert in q:
        if cert.pemAsString() == pem:
            return True

def _importCertificate(x509, fingerprint, trust, repView):
    pem = x509.as_pem()
    if _isInRepository(repView, pem):
        raise ValueError, 'X.509 certificate is already in the repository'
        
    subjectCommonName = x509.get_subject().CN
    asText = x509.as_text()
    
    type = _certificateType(x509)
    if type == 'root':
        if not x509.verify():
            raise ValueError, 'X.509 certificate does not verify'
    
    cert = Certificate(view=repView)
    text = cert.getAttributeAspect('pem', 'type').makeValue(pem,
                                                            compression=None)
    cert.pem = text
    text = cert.getAttributeAspect('asText', 'type').makeValue(asText)
    cert.asText = text
    cert.type = type
    cert.trust = trust
    cert.fingerprintAlgorithm = 'sha1'
    cert.fingerprint = fingerprint
    cert.subjectCommonName = subjectCommonName

    qName = TRUSTED_SITE_CERTS_QUERY_NAME
    q = repView.findPath('//Queries/%s' %(qName))
    if q is None:
        p = repView.findPath('//Queries')
        k = repView.findPath('//Schema/Core/Query')
        q = Query.Query(qName, p, k, u'for i in "//parcels/osaf/framework/certstore/schema/Certificate" where i.type == "site" and i.trust == %d' % (TRUST_AUTHENTICITY))
        notificationItem = repView.findPath('//parcels/osaf/framework/certstore/schema/dummyCertNotification')
        q.subscribe(notificationItem, 'handle', True, True)
    
    repView.commit()


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
        type = _certificateType(x509)
        # Note: the order of choices must match the selections code below
        choices = ["Trust the authenticity of this certificate."]
        if type == 'root':
            choices += ["Trust this certificate to sign site certificates."]

        dlg = wx.MultiChoiceDialog(wx.GetApp().mainFrame,
                                   "Do you want to import this certificate?\n" +
                                   "Type: " + type +
                                   "\nSHA1 fingerprint: " + fingerprint +
                                   "\n" + x509.as_text(),
                                   "Import check",
                                   choices=choices)
        trust = 0
        if dlg.ShowModal() == wx.ID_OK:
            selections = dlg.GetSelections()
            dlg.Destroy()
            # Note: this code must match the choices above
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
        # XXX Inform the user what went wrong so they can figure out how to
        # XXX fix this.
        application.dialogs.Util.ok(wx.GetApp().mainFrame, "Error", 
            "Could not add certificate from: " + path + 
            "\nCheck the path and try again.")
        return


def CreateSidebarView(repView, cpiaView):
    sidebar = ItemCollection.ItemCollection(view=repView)
    sidebar.displayName = 'Certificate Store'
    sidebar._rule = ALL_CERTS_QUERY

    q = _allCertificatesQuery(repView)
    
    for item in q:
        sidebar.add(item)

    cpiaView.postEventByName('AddToSidebarWithoutCopying',
                             {'items': [sidebar]})

# XXX end store.py
###############

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

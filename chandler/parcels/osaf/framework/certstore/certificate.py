"""
Certificate

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""
__parcel__ = "osaf.framework.certstore"

import logging

import wx
import application
from application import schema
import osaf.framework.blocks.Block as Block
import application.Globals as Globals
from osaf import pim
import osaf.framework.blocks.detail.Detail as Detail
from osaf.framework.certstore import notification
from osaf.framework.certstore import dialogs
import M2Crypto.X509 as X509
import M2Crypto.util as util
import M2Crypto.EVP as EVP
from application.dialogs import ImportExport
from i18n import OSAFMessageFactory as _
import os

# XXX Should be done using ref collections instead?
import repository.query.Query as Query

log = logging.getLogger(__name__)

TRUST_AUTHENTICITY = 1
TRUST_SITE         = 2

TYPE_ROOT          = 'root'
TYPE_SITE          = 'site'

TRUSTED_SITE_CERTS_QUERY_NAME = 'sslTrustedSiteCertificatesQuery'

# @@@ Not used anymore, replaced by KindCollection
# ALL_CERTS_QUERY = u'for i in "//parcels/osaf/framework/certstore/Certificate" where True'


class typeEnum(schema.Enumeration):
    schema.kindInfo(displayName = "Type Enumeration")
    values = TYPE_ROOT, TYPE_SITE


class CertificateStore(pim.KindCollection):
    schema.kindInfo(displayName = "Certificate Store")

class Certificate(pim.ContentItem):

    schema.kindInfo(displayName = "Certificate")

    who = schema.One(redirectTo = 'subjectCommonName')
    displayName = schema.One(redirectTo = 'subjectCommonName')
    about = schema.One(
        doc = "Issues: type would make more sense, but it isn't supported for summary view.",
        redirectTo = 'trust',
    )
    date = schema.One(redirectTo = 'createdOn')
    subjectCommonName = schema.One(
        schema.String,
        displayName = _('Subject commonName'),
        doc = 'Subject commonName.',
    )
    type = schema.One(
        typeEnum,
        displayName = _('Certificate type'),
        doc = 'Certificate type.',
        initialValue = TYPE_ROOT,
    )
    trust = schema.One(
        schema.Integer,
        displayName = _('Trust'),
        doc = 'A certificate can have no trust assigned to it, or any combination of 1=trust authenticity of certificate, 2=trust to issue site certificates.',
    )
    pem = schema.One(
        schema.Lob,
        displayName = _('PEM'),
        doc = 'An X.509 certificate in PEM format.',
    )
    asText = schema.One(
        schema.Lob,
        displayName = _('Human readable certificate value'),
        doc = 'An X.509 certificate in human readable format.',
    )
    fingerprintAlgorithm = schema.One(
        schema.String,
        displayName = _('fingerprint algorithm'),
        doc = 'A name of a hash algorithm that was used to compute fingerprint.',
    )
    fingerprint = schema.One(
        schema.String,
        doc = 'A hash of the certificate using algorithm named in fingerprintAlgorithm attribute.',
    )

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


def fingerprint(x509, md='sha1'):
    """
    Return the fingerprint of the X509 certificate.
    
    @param x509: X509 object.
    @type x509:  M2Crypto.X509.X509
    @param md:   The message digest algorithm.
    @type md:    str
    """
    der = x509.as_der()
    md = EVP.MessageDigest(md)
    md.update(der)
    digest = md.final()
    return hex(util.octx_to_num(digest))

###
# XXX begin store.py

class CertificateViewController(Block.Block):
    def onCertificateViewBlockEvent(self, event):
        createSidebarView(self.itsView, Globals.views[0])


class CertificateImportController(Block.Block):
    def onCertificateImportBlockEvent(self, event):
        importCertificateDialog(self.itsView)


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
            type = TYPE_ROOT
        elif _isSiteCertificate(x509):
            type = TYPE_SITE
    except LookupError:
        subject = x509.get_subject()
        issuer = x509.get_issuer()
        if subject.CN == issuer.CN:
            type = TYPE_ROOT
        elif _isSiteCertificate(x509):
            type = TYPE_SITE
                
    if type is None:
        raise Exception, 'could not determine certificate type'
        
    return type

# @@@MOR -- Not used anymore, replaced by KindCollection
#
# def _allCertificatesQuery(repView):
#     qName = 'allCertificatesQuery'
#     q = repView.findPath('//Queries/%s' %(qName))
#     if q is None:
#         p = repView.findPath('//Queries')
#         k = repView.findPath('//Schema/Core/Query')
#         q = Query.Query(qName, p, k, ALL_CERTS_QUERY)
#         notificationItem = repView.findPath('//parcels/osaf/framework/certstore/dummyCertNotification')
#         q.subscribe(notificationItem, 'handle', True, True)
# 
#     return q

def _isInRepository(repView, pem):
    # XXX This could be optimized by querying based on some cheap field,
    # XXX like subjectCommonName, which would typically return just 0 or 1
    # XXX hit. But I don't want to leave query items laying around either.
    q = pim.KindCollection(view=repView)
    q.kind = repView.findPath('//parcels/osaf/framework/certstore/Certificate')

    for cert in q:
        if cert.pemAsString() == pem:
            return True

def importCertificate(x509, fingerprint, trust, repView):
    """
    Import X.509 certificate.
    
    @param x509:        The X.509 certificate to import
    @param fingerprint: The fingerprint of the certificate (in SHA1)
    @param trust:       The trust value for this certificate
    """
    pem = x509.as_pem()
    if _isInRepository(repView, pem):
        raise ValueError, 'X.509 certificate is already in the repository'
        
    subjectCommonName = x509.get_subject().CN
    asText = x509.as_text()
    
    type = _certificateType(x509)
    if type == TYPE_ROOT:
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
        q = Query.Query(qName, p, k, u'for i in "//parcels/osaf/framework/certstore/Certificate" where i.type == "%s" and i.trust == %d' % (TYPE_SITE, TRUST_AUTHENTICITY))
        notificationItem = repView.findPath('//parcels/osaf/framework/certstore/dummyCertNotification')
        q.subscribe(notificationItem, 'handle', True, True)
    
    repView.commit()


def importCertificateDialog(repView):
    res = ImportExport.showFileDialog(wx.GetApp().mainFrame,
                                      _("Choose a certificate to import"),
                                      "", 
                                      "", 
                                      _("PEM files|*.pem;*.crt|All files (*.*)|*.*"),
                                      wx.OPEN | wx.HIDE_READONLY)

    (cmd, dir, filename) = res

    if cmd  != wx.ID_OK:
        return

    path = os.path.join(dir, filename)

    try: 
        x509 = X509.load_cert(path)

        fprint = fingerprint(x509)
        type = _certificateType(x509)
        # Note: the order of choices must match the selections code below
        choices = [_("Trust the authenticity of this certificate.")]
        if type == TYPE_ROOT:
            choices += [_("Trust this certificate to sign site certificates.")]

        dlg = dialogs.ImportCertificateDialog(wx.GetApp().mainFrame,
                                   type,
                                   x509,
                                   choices)
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

        importCertificate(x509, fprint, trust, repView)
    except Exception, e:
        log.exception(e)
        # XXX Inform the user what went wrong so they can figure out how to
        # XXX fix this.
        application.dialogs.Util.ok(wx.GetApp().mainFrame, _("Error"), 
            _("Could not add certificate from: %s\nCheck the path and try again.") % path)
        return


def createSidebarView(repView, cpiaView):
    """
    Add the certificate store entry into the sidebar.
    """
    # First see if the certificate store already is in the sidebar, and if so
    # don't add more entries.
    sidebar = schema.ns('osaf.views.main', repView).sidebarItemCollection
    for item in sidebar:
        # XXX It is kind of heavy-weight to have the CertificateStore class
        # XXX just so we can see if this collection is certstore. Besides,
        # XXX isinstance is bad.
        if isinstance(item, CertificateStore):
            return

    certstore = CertificateStore(view=repView)
    
    # XXX Why isn't this picked from the CertificateStore class?
    certstore.displayName = 'Certificate Store'
    
    # XXX It seems like it should be possible to put this in the CertificateStore
    # XXX class to make this happen automatically?
    certstore.kind = repView.findPath('//parcels/osaf/framework/certstore/Certificate')

    # @@@MOR -- Transitioning to new Collection world.  Does specifying
    # the kind above automatically populate the collection?  That makes the
    # following commented-out code unnecessary:

    # certstore._rule = ALL_CERTS_QUERY

    # q = _allCertificatesQuery(repView)

    # for item in q:
    #     certstore.add(item)

    cpiaView.postEventByName('AddToSidebarWithoutCopying',
                             {'items': [certstore]})

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

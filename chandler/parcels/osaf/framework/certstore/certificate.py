"""
Certificate

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""
__parcel__ = "osaf.framework.certstore"

__all__ = ['Certificate', 'CertificateStore',
           'importCertificate', 'importCertificateDialog', 'createSidebarView']

import os, logging

import wx
import M2Crypto.X509 as X509
import M2Crypto.util as util
import M2Crypto.EVP as EVP

import application
from application import schema
import application.Globals as Globals
from osaf import pim
from application.dialogs import ImportExport
from i18n import OSAFMessageFactory as _
from osaf.pim.collections import FilteredCollection
from osaf.framework.certstore import utils, dialogs, constants

log = logging.getLogger(__name__)


class typeEnum(schema.Enumeration):
    schema.kindInfo(displayName = "Type Enumeration")
    values = constants.TYPE_ROOT, constants.TYPE_SITE


class CertificateStore(pim.KindCollection):
    schema.kindInfo(displayName = _("Certificate Store"))
    
    def __init__(self, *args, **kw):
        super(CertificateStore, self).__init__(*args, **kw)
        # XXX Why isn't this picked from the kindInfo above?
        self.displayName = _('Certificate Store')

        self.kind = self.itsView.findPath('//parcels/osaf/framework/certstore/Certificate')


class Certificate(pim.ContentItem):

    schema.kindInfo(displayName = "Certificate")

    who = schema.One(redirectTo = 'displayName')
    displayName = schema.One(
        schema.String,
        displayName = _('Display Name'),
        doc = 'Display Name.',
    )
    about = schema.One(
        doc = "Issues: type would make more sense, but it isn't supported for summary view.",
        redirectTo = 'trust',
    )
    date = schema.One(redirectTo = 'createdOn')
    type = schema.One(
        typeEnum,
        displayName = _('Certificate type'),
        doc = 'Certificate type.',
        initialValue = constants.TYPE_ROOT,
    )
    trust = schema.One(
        schema.Integer,
        displayName = _('Trust'),
        defaultValue = 0,
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
        return bool(self.trust & constants.TRUST_AUTHENTICITY)
    def setAuthenticityBit(self, authBit):
        if authBit:
            self.trust |= constants.TRUST_AUTHENTICITY
        else:
            self.trust &= ~constants.TRUST_AUTHENTICITY
    authenticityBit = property(getAuthenticityBit, setAuthenticityBit,
                               doc='Authenticity bit.')

    def getSiteBit(self):
        return bool(self.trust & constants.TRUST_SITE)
    def setSiteBit(self, siteBit):
        if siteBit:
            self.trust |= constants.TRUST_SITE
        else:
            self.trust &= ~constants.TRUST_SITE
    siteBit = property(getSiteBit, setSiteBit,
                       doc='Site bit.')


###
# XXX begin store.py

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
            type = constants.TYPE_ROOT
        elif _isSiteCertificate(x509):
            type = constants.TYPE_SITE
    except LookupError:
        subject = x509.get_subject()
        issuer = x509.get_issuer()
        if subject.CN == issuer.CN:
            type = constants.TYPE_ROOT
        elif _isSiteCertificate(x509):
            type = constants.TYPE_SITE
                
    if type is None:
        raise Exception, 'could not determine certificate type'
        
    return type

def _isInRepository(repView, pem):
    # XXX This could be optimized by querying based on some cheap field,
    # XXX which would typically return just 0 or 1
    # XXX hit. But I don't want to leave query items laying around either.
    q = utils.getExtent(Certificate, view=repView)

    for cert in q:
        if cert.pemAsString() == pem:
            return True
    
    return False

def importCertificate(x509, fingerprint, trust, repView):
    """
    Import X.509 certificate.
    
    @param x509:        The X.509 certificate to import
    @param fingerprint: The fingerprint of the certificate (in SHA1)
    @param trust:       The trust value for this certificate
    """
    pem = x509.as_pem()
    if _isInRepository(repView, pem):
        raise ValueError('X.509 certificate is already in the repository')
        
    commonName = x509.get_subject().CN
    asText = x509.as_text()
    
    type = _certificateType(x509)
    if type == constants.TYPE_ROOT:
        if not x509.verify():
            raise ValueError('X.509 certificate does not verify')
    
    lobType = schema.itemFor(schema.Lob, repView)
    pem = lobType.makeValue(pem, compression=None)
    text = lobType.makeValue(asText)
    
    cert = Certificate(view=repView,
                       trust=trust,
                       type=type,
                       fingerprint=fingerprint,
                       fingerprintAlgorithm='sha1',
                       displayName=commonName,
                       pem=pem,
                       asText=text)

    # XXX Why is this collection created here, as it is not used here?
    q = repView.findPath('//userdata/%s' %(constants.TRUSTED_SITE_CERTS_QUERY_NAME))
    if q is None:
        q = FilteredCollection(constants.TRUSTED_SITE_CERTS_QUERY_NAME, view=repView)
        q.source = utils.getExtent(Certificate, repView)
        q.filterExpression = 'item.type == "%s" and item.trust == %d' % (constants.TYPE_SITE, constants.TRUST_AUTHENTICITY)
        q.filterAttributes = ['type', 'trust']
    
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

        fprint = utils.fingerprint(x509)
        type = _certificateType(x509)
        # Note: the order of choices must match the selections code below
        choices = [_("Trust the authenticity of this certificate.")]
        if type == constants.TYPE_ROOT:
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
                    trust |= constants.TRUST_AUTHENTICITY
                if sel == 1:
                    trust |= constants.TRUST_SITE
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
    sidebar = schema.ns('osaf.views.main', repView).sidebarCollection
    for item in sidebar:
        # XXX It is kind of heavy-weight to have the CertificateStore class
        # XXX just so we can see if this collection is certstore. Besides,
        # XXX isinstance is bad.
        if isinstance(item, CertificateStore):
            cpiaView.postEventByName('RequestSelectSidebarItem',
                                     {'item': item})
            return

    certstore = CertificateStore(view=repView)
    
    cpiaView.postEventByName('AddToSidebarWithoutCopyingAndSelectFirst',
                             {'items': [certstore]})

# XXX end store.py
###############

#   Copyright (c) 2005-2006 Open Source Applications Foundation
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

"""
Certificate
"""

__parcel__ = "osaf.framework.certstore"

__all__ = ['Certificate', 'importCertificate',
           'importCertificateDialog', 'findCertificate', 'certificateType']

import os, logging, sys

import wx
import M2Crypto.X509 as X509

import application
from application import schema
from osaf import pim
from application.dialogs import Util
from i18n import OSAFMessageFactory as _
from osaf import messages
from osaf.pim.collections import FilteredCollection
from osaf.framework.certstore import utils, dialogs, constants


log = logging.getLogger(__name__)

class typeEnum(schema.Enumeration):
    """
    Type enumeration
    @see: U{model<../model/parcels/osaf/framework/certstore/typeEnum/index.html>}
    """
    schema.kindInfo(displayName = u"Type Enumeration")
    values = constants.TYPE_ROOT, constants.TYPE_SITE

class Certificate(pim.ContentItem):
    """
    Certificate

    @see: U{model<../model/parcels/osaf/framework/certstore/Certificate/index.html>}
    """

    schema.kindInfo(displayName = _(u"Certificate"))

    who = schema.One(redirectTo = 'displayName')
    displayName = schema.One(
        schema.Text, displayName = _(u'Display Name'),
        doc = 'Display Name.',
    )
    about = schema.One(
        doc = "Issues: type would make more sense, but it isn't supported for summary view.",
        redirectTo = 'trust',
    )
    date = schema.One(redirectTo = 'createdOn')
    type = schema.One(
        typeEnum,
        displayName = _(u'Certificate type'),
        doc = 'Certificate type.',
        initialValue = constants.TYPE_ROOT,
    )
    trust = schema.One(
        schema.Integer,
        displayName = _(u'Trust'),
        defaultValue = 0,
        doc = 'A certificate can have no trust assigned to it, or any combination of 1=trust authenticity of certificate, 2=trust to issue site certificates.',
    )
    pem = schema.One(
        schema.Lob,
        displayName = _(u'PEM'),
        doc = 'An X.509 certificate in PEM format.',
    )
    asText = schema.One(
        schema.Lob,
        displayName = _(u'Human readable certificate value'),
        doc = 'An X.509 certificate in human readable format.',
    )
    fingerprintAlgorithm = schema.One(
        schema.Text,
        displayName = _(u'fingerprint algorithm'),
        doc = 'A name of a hash algorithm that was used to compute fingerprint.',
    )
    fingerprint = schema.One(
        schema.Text,
        doc = 'A hash of the certificate using algorithm named in fingerprintAlgorithm attribute.',
    )

    def pemAsString(self):
        """
        Get the pem attribute (which is stored as a LOB) as a str.

        @return: pem as str
        @rtype:   str
        """
        # M2Crypto needs this to be str rather than unicode - safe conversion
        return str(self.pem.getReader().read())

    def getAsTextAsString(self):
        """
        Get the asText attribute (which is stored as a LOB) as a str.

        @return: asText as unicode
        @rtype:  unicode
        """
        return self.asText.getPlainTextReader().read()

    asTextAsString = pim.Calculated(schema.Text, u"body",
        basedOn=('asText',),
        fget=getAsTextAsString,
        doc="asText attribute as a string")

    def asX509(self):
        """
        Get the pem (which is stored as a LOB) as a C{M2Crypto.X509.X509}
        instance.

        @return: pem as C{M2Crypto.X509.X509}.
        @rtype:  C{M2Crypto.X509.X509}
        """
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

    def isAttributeModifiable(self, attribute):
        # None of these attributes should be edited by the user.
        if attribute in ['date', 'type', 'fingerprintAlgorithm', 
                                 'fingerprint', 'asTextAsString' ]:
            return False
        return super(Certificate, self).isAttributeModifiable(attribute)


def _isRootCertificate(x509):
    # XXX This will need tweaks
    # XXX Should use OpenSSL itself if possible
    # XXX X509_check_ca, X509_check_purpose
    root = False

    try:
        root = x509.get_ext('basicConstraints').get_value().find('CA:TRUE') > -1
        log.debug('"basicConstraints" contained "CA:TRUE": %s' % root)
    except LookupError:
        pass

    if not root:
        try:
            root = x509.get_ext('keyUsage').get_value().find('Certificate Sign') > -1
            log.debug('"keyUsage" contained "Certificate Sign": %s' % root)
        except LookupError:
            pass
    
    if not root:
        try:
            root = x509.get_ext('nsCertType').get_value().find('SSL CA') > -1
            log.debug('"nsCertType" contained "SSL CA": %s' % root)
        except LookupError:
            pass
    
    if not root:
        subject = x509.get_subject()
        issuer = x509.get_issuer()
        if subject.as_text() == issuer.as_text():
            root = True
        log.debug('subject and issuer matched: %s' % root)

    return root

def _isSiteCertificate(x509):
    # XXX This will need tweaks
    # XXX Should use OpenSSL itself if possible
    # XXX X509_check_purpose
    site = False
    
    try:
        site = x509.get_ext('extendedKeyUsage').get_value().find('TLS Web Server Authentication') > -1
        log.debug('"extendedKeyUsage" contained "TLS Web Server Authentication": %s' % site)
    except LookupError:
        pass
    
    if not site:
        try:
            site = x509.get_ext('nsCertType').get_value().find('SSL Server') > -1
            log.debug('"nsCertType" contained "SSL Server": %s' % site)
        except LookupError:
            pass

    if not site:
        try:
            host = x509.get_ext('subjectAltName').get_value()
            host = host.lower()
            if host[:4] == 'dns:':
                site = True
            log.debug('"subjectAltName" contained "DNS": %s' % site)
        except LookupError:
            pass

    if not site:
        commonName = x509.get_subject().CN
        if commonName.find(' ') < 0 and commonName.find('.') > -1:
            site = True
        elif commonName.replace('.','').isdigit():
            site = True
        elif commonName == 'localhost':
            site = True
        # XXX We could still miss certificates that are issued for
        # XXX local, named hosts other than localhost.
        log.debug('"commonName" indicated a site certificate: %s' % site)

    return site


def certificateType(x509, typeHint=None):
    """
    Determine certificate type.
    
    @param typeHint: We try to see if the certificate could be this type first,
                     before trying any other types.
    """
    type = None
    
    if typeHint == constants.TYPE_SITE:
        if _isSiteCertificate(x509):
            type = constants.TYPE_SITE

    if type is None:
        if _isRootCertificate(x509):
            type = constants.TYPE_ROOT
        elif _isSiteCertificate(x509):
            type = constants.TYPE_SITE

    if type is None:
        raise utils.CertificateException(_(u'Could not determine certificate type.'))

    return type

def findCertificate(repView, pem):
    """
    See if the certificate is stored in the repository.
    """
    q = utils.getExtent(Certificate, view=repView)

    for cert in q:
        if cert.pemAsString() == pem:
            return cert

    return None

def importCertificate(x509, fingerprint, trust, repView, typeHint=None):
    """
    Import X.509 certificate.

    @param x509:        The X.509 certificate to import
    @param fingerprint: The fingerprint of the certificate (in SHA1)
    @param trust:       The trust value for this certificate
    """
    pem = x509.as_pem()
    if findCertificate(repView, pem) is not None:
        raise utils.CertificateException(_(u'This certificate has already been imported.'))

    commonName = x509.get_subject().CN

    if commonName is None:
        commonName = ""

    asText = x509.as_text()

    type = certificateType(x509, typeHint)
    if type == constants.TYPE_ROOT:
        if not x509.verify():
            raise utils.CertificateException(_(u'Unable to verify the certificate.'))

    lobType = schema.itemFor(schema.Lob, repView)
    pem = lobType.makeValue(pem, compression=None)
    text = lobType.makeValue(asText)

    #XXX [i18n] Can a commonName contain non-ascii characters?
    cert = Certificate(itsView=repView,
                       trust=trust,
                       type=type,
                       fingerprint=fingerprint,
                       fingerprintAlgorithm='sha1',
                       displayName=unicode(commonName),
                       pem=pem,
                       asText=text)
    
    log.info('Imported certificate: CN=%s, type=%s, fp=%s' % (commonName,
                                                              type,
                                                              fingerprint))
    return cert


def importCertificateDialog(repView):
    """
    Let the user import a certificate. First brings up a file selection
    dialog, then asks for trust settings for the certificate being imported.
    """
    certificate = None
    app = wx.GetApp()
    res = Util.showFileDialog(app.mainFrame,
                              _(u"Choose a certificate to import"),
                              u"", 
                              u"", 
                              _(u"PEM files|*.pem;*.crt|All files (*.*)|*.*"),
                              wx.OPEN | wx.HIDE_READONLY)

    (cmd, dir, filename) = res

    if cmd  == wx.ID_OK:
        # dir and filename are unicode
        path = os.path.join(dir, filename)
    
        try: 
            x509 = X509.load_cert(path)
    
            fprint = utils.fingerprint(x509)
            type = certificateType(x509)
            # Note: the order of choices must match the selections code below
            choices = [_(u"Trust the authenticity of this certificate.")]
            if type == constants.TYPE_ROOT:
                choices += [_(u"Trust this certificate to sign site certificates.")]
    
            dlg = dialogs.ImportCertificateDialog(app.mainFrame,
                                       type,
                                       fprint,
                                       x509,
                                       choices)
            trust = 0
            if dlg.ShowModal() == wx.ID_OK:
                selections = dlg.GetSelections()
                # Note: this code must match the choices above
                for sel in selections:
                    if sel == 0:
                        trust |= constants.TRUST_AUTHENTICITY
                    if sel == 1:
                        trust |= constants.TRUST_SITE
                certificate = importCertificate(x509, fprint, trust, repView)
            dlg.Destroy()
    
        except utils.CertificateException, e:
            application.dialogs.Util.ok(app.mainFrame, messages.ERROR, e.__unicode__())
    
        except Exception, e:
            log.exception(e)
            application.dialogs.Util.ok(app.mainFrame, messages.ERROR,
                _(u"Could not add certificate from: %(path)s\nCheck the path and try again.") % {'path': path})
    return certificate

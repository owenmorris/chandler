#   Copyright (c) 2005-2007 Open Source Applications Foundation
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
           'importCertificateDialog', 'findCertificate', 'certificatePurpose']

import os, logging, sys

import wx
from M2Crypto import X509, m2

import application
from application import schema
from osaf import pim
from application.dialogs import Util
from i18n import ChandlerMessageFactory as _
from osaf import messages
from osaf.pim.collections import FilteredCollection
from osaf.framework.certstore import utils, dialogs, constants


log = logging.getLogger(__name__)

class Certificate(pim.ContentItem):
    """
    Certificate

    @see: U{model<../model/parcels/osaf/framework/certstore/Certificate/index.html>}
    """

    purpose = schema.One(
        schema.Integer,
        doc = 'Certificate purpose.',
        initialValue = constants.PURPOSE_CA,
    )
    trust = schema.One(
        schema.Integer,
        defaultValue = constants.TRUST_NONE,
        doc = 'A certificate can have no trust assigned to it, or any combination of 1=trust authenticity of certificate, 2=trust to issue server certificates.',
    )
    pem = schema.One(
        schema.Lob,
        doc = 'An X.509 certificate in PEM format.',
    )
    asText = schema.One(
        schema.Lob,
        doc = 'An X.509 certificate in human readable format.',
    )
    fingerprintAlgorithm = schema.One(
        schema.Text,
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

    asTextAsString = schema.Calculated(schema.Text,
        basedOn=(asText,),
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

    def isAttributeModifiable(self, attribute):
        # None of these attributes should be edited by the user.
        if attribute in ['date', 'purpose', 'fingerprintAlgorithm',
                                 'fingerprint', 'asTextAsString' ]:
            return False
        return super(Certificate, self).isAttributeModifiable(attribute)
    
    @schema.observer(purpose, trust, pem)
    def changed(self, op, name):
        """
        Get a change notification for an attribute change. This happens
        on item creation as well as normal attribute change (including
        deletion), but not on item deletion.
        """
        # XXX Certificate should not need to know about ssl.contextCache
        from osaf.framework.certstore import ssl
        ssl.contextCache = None
        
    def onItemDelete(self, view, isDeferring):
        """
        Get a change notification for an item deletion.
        """
        self.changed('remove', None)

def _isCACertificate(x509):
    ca = False
    
    try:
        # This works with OpenSSL 0.9.8 or later
        ca = x509.check_ca() > 0
        log.debug('check_ca(): %s' % ca)
    except AttributeError:
        # Our backup algorithm for older OpenSSL
        try:
            ca = x509.get_ext('basicConstraints').get_value().find('CA:TRUE') > -1
            log.debug('"basicConstraints" contained "CA:TRUE": %s' % ca)
        except LookupError:
            pass
    
        if not ca:
            try:
                ca = x509.get_ext('keyUsage').get_value().find('Certificate Sign') > -1
                log.debug('"keyUsage" contained "Certificate Sign": %s' % ca)
            except LookupError:
                pass
    
        if not ca:
            try:
                ca = x509.get_ext('nsCertType').get_value().find('SSL CA') > -1
                log.debug('"nsCertType" contained "SSL CA": %s' % ca)
            except LookupError:
                pass
    
        if not ca:
            subject = x509.get_subject()
            issuer = x509.get_issuer()
            if subject.as_text() == issuer.as_text():
                ca = True
            log.debug('subject and issuer matched: %s' % ca)

    return ca

def _isServerCertificate(x509):
    server = False

    try:
        # Works with M2Crypto 0.17 and later
        server = x509.check_purpose(m2.X509_PURPOSE_SSL_SERVER, 0) or \
                 x509.check_purpose(m2.X509_PURPOSE_NS_SSL_SERVER, 0)
        log.debug('check_purpose(): %s' % server)
    except:
        try:
            server = x509.get_ext('extendedKeyUsage').get_value().find('TLS Web Server Authentication') > -1
            log.debug('"extendedKeyUsage" contained "TLS Web Server Authentication": %s' % server)
        except LookupError:
            pass
    
        if not server:
            try:
                server = x509.get_ext('nsCertType').get_value().find('SSL Server') > -1
                log.debug('"nsCertType" contained "SSL Server": %s' % server)
            except LookupError:
                pass
    
        if not server:
            try:
                host = x509.get_ext('subjectAltName').get_value()
                host = host.lower()
                if host[:4] == 'dns:':
                    server = True
                log.debug('"subjectAltName" contained "DNS": %s' % server)
            except LookupError:
                pass
    
        if not server:
            commonName = x509.get_subject().CN or ''
            if commonName.find(' ') < 0 and commonName.find('.') > -1:
                server = True
            elif commonName.replace('.','').isdigit():
                server = True
            elif commonName == 'localhost':
                server = True
            # XXX We could still miss certificates that are issued for
            # XXX local, named hosts other than localhost.
            log.debug('"commonName" indicated a server certificate: %s' % server)

    return server


def certificatePurpose(x509):
    """
    Determine certificate purposes.
    """
    purpose = 0
    
    if _isCACertificate(x509):
        purpose |= constants.PURPOSE_CA
    
    if _isServerCertificate(x509):
        purpose |= constants.PURPOSE_SERVER

    if purpose == 0:
        raise utils.CertificateException(_(u'Could not determine certificate purpose.'))

    return purpose

def findCertificate(repView, pem):
    """
    See if the certificate is stored in the repository.
    """
    q = utils.getExtent(Certificate, view=repView)

    for cert in q:
        if cert.pemAsString() == pem:
            return cert

    return None

def importCertificate(x509, fingerprint, trust, repView):
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

    purpose = certificatePurpose(x509)
    if purpose & constants.PURPOSE_CA:
        if not x509.verify():
            raise utils.CertificateException(_(u'Unable to verify the certificate.'))

    lobType = schema.itemFor(schema.Lob, repView)
    pem = lobType.makeValue(pem, compression=None)
    text = lobType.makeValue(asText)

    #XXX [i18n] Can a commonName contain non-ascii characters?
    cert = Certificate(itsView=repView,
                       trust=trust,
                       purpose=purpose,
                       fingerprint=fingerprint,
                       fingerprintAlgorithm='sha1',
                       displayName=unicode(commonName),
                       pem=pem,
                       asText=text)

    log.info('Imported certificate: CN=%s, purpose=%s, fp=%s' % (commonName,
                                                                 purpose,
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
                              wx.OPEN)

    (cmd, dir, filename) = res

    if cmd  == wx.ID_OK:
        # dir and filename are unicode
        path = os.path.join(dir, filename)

        try:
            x509 = X509.load_cert(path)

            fprint = utils.fingerprint(x509)
            purpose = certificatePurpose(x509)
            # Note: the order of choices must match the selections code below
            choices = [_(u"Trust the authenticity of this certificate.")]
            if purpose & constants.PURPOSE_CA:
                choices += [_(u"Trust this certificate to sign site certificates.")]

            dlg = dialogs.ImportCertificateDialog(app.mainFrame,
                                       purpose,
                                       fprint,
                                       x509,
                                       choices)
            trust = constants.TRUST_NONE
            if dlg.ShowModal() == wx.ID_OK:
                selections = dlg.GetSelections()
                # Note: this code must match the choices above
                for sel in selections:
                    if sel == 0:
                        trust |= constants.TRUST_AUTHENTICITY
                    if sel == 1:
                        trust |= constants.TRUST_SERVER
                certificate = importCertificate(x509, fprint, trust, repView)
            dlg.Destroy()

        except utils.CertificateException, e:
            application.dialogs.Util.ok(app.mainFrame, messages.ERROR, e.__unicode__())

        except Exception, e:
            log.exception(e)
            application.dialogs.Util.ok(app.mainFrame, messages.ERROR,
                _(u"Could not add certificate from: %(path)s\nCheck the path and try again.") % {'path': path})
    return certificate

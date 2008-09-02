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

from osaf import ChandlerException

__all__ = ['MailException', 'IMAPException', 'SMTPException',
           'POPException', 'IMAPTimeoutException']

class MailException(ChandlerException):
    """Base class for all Chandler mail related exceptions"""

class IMAPException(MailException):
    """Base class for all Chandler IMAP based exceptions"""

class IMAPTimeoutException(IMAPException):
    """IMAP client timeout exception"""

class SMTPException(MailException):
    """Base class for all Chandler SMTP based exceptions"""

class POPException(MailException):
    """Base class for all Chandler POP based exceptions"""

__SMTP_PREFIX        = "twisted.mail.smtp."
__IMAP4_PREFIX       = "twisted.mail.imap4."
__TWISTED_PREFIX     = "twisted.internet.error."
__MAILSERVICE_PREFIX = "osaf.mail.errors."

AUTH_DECLINED_ERROR       = __SMTP_PREFIX + "AUTHDeclinedError"
TLS_ERROR                 = __SMTP_PREFIX + "TLSError"
SMTP_DELIVERY_ERROR       = __SMTP_PREFIX + "SMTPDeliveryError"
SMTP_CONNECT_ERROR        = __SMTP_PREFIX + "SMTPConnectError"
SMTP_PROTOCOL_ERROR       = __SMTP_PREFIX + "SMTPProtocolError"
CONNECT_ERROR             = __TWISTED_PREFIX + "ConnectError"
CONNECT_BIND_ERROR        = __TWISTED_PREFIX + "ConnectBindError"
UNKNOWN_HOST_ERROR        = __TWISTED_PREFIX + "UnknownHostError"
TIMEOUT_ERROR             = __TWISTED_PREFIX + "TimeoutError"
SSL_ERROR                 = __TWISTED_PREFIX + "SSLError"
DNS_LOOKUP_ERROR          = __TWISTED_PREFIX + "DNSLookupError"
CONNECTION_REFUSED_ERROR  = __TWISTED_PREFIX + "ConnectionRefusedError"
MAIL_EXCEPTION            = __MAILSERVICE_PREFIX + "MailException"
IMAP_EXCEPTION            = __MAILSERVICE_PREFIX + "IMAPException"
SMTP_EXCEPTION            = __MAILSERVICE_PREFIX + "SMTPException"
POP_EXCEPTION             = __MAILSERVICE_PREFIX + "POPException"

""" Contains common transport error codes used by the mail service"""
__offset = 600

DNS_LOOKUP_CODE         = __offset + 1
DELIVERY_CODE           = __offset + 2
PROTOCOL_CODE           = __offset + 3
CONNECTION_CODE         = __offset + 4
BIND_CODE               = __offset + 5
UNKNOWN_HOST_CODE       = __offset + 6
TIMEOUT_CODE            = __offset + 8
SSL_CODE                = __offset + 9
CONNECTION_REFUSED_CODE = __offset + 10
UNKNOWN_CODE            = __offset + 11
MISSING_VALUE_CODE      = __offset + 12
M2CRYPTO_CODE           = __offset + 13
SMTP_EXCEPTION_CODE     = __offset + 14

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Contains common transport error codes used by the mail service"""
__offset = 600

DNS_LOOKUP_ERROR = __offset + 1
DELIVERY_ERROR = __offset + 2
PROTOCOL_ERROR = __offset + 3
CONNECTION_ERROR = __offset + 4
BIND_ERROR = __offset + 5
UNKNOWN_HOST_ERROR = __offset + 6
TIMEOUT_ERROR = __offset + 8
SSL_ERROR = __offset + 9
CONNECTION_REFUSED_ERROR = __offset + 10
UNKNOWN_ERROR = __offset + 11

ERROR_LOOKUP = \
{ 
    DNS_LOOKUP_ERROR: "DNS Lookup Error",
    DELIVERY_ERROR: "Delivery Error",
    PROTOCOL_ERROR: "Protocol Error",
    CONNECTION_ERROR: "Connection Error",
    BIND_ERROR: "TCP Bind Error",
    UNKNOWN_HOST_ERROR: "Unknown Host Error",
    TIMEOUT_ERROR: "Connection Timeout Error",
    SSL_ERROR: "SSL Error",
    CONNECTION_REFUSED_ERROR: "Connection Refused Error",
    UNKNOWN_ERROR: "Unknown Error"
}


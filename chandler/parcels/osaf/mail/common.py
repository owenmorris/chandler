__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Contains common functionality shared across the Mail Domain (SMTP, IMAP4, POP3) """


import email as email
import email.Message as Message
import email.Utils as Utils


def getChandlerTransportMessage():
    message = """Subject: ***FOR CHANDLER INTERNAL USE - DO NOT DELETE ***

    This message is used for Chandler to Chandler communication and is
    not intended to be viewed by the user. Please do not delete this message
    as Chandler will manage this email automatically for you.

    """

    return email.message_from_string(message)

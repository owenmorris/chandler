__revision__  = "$Revision: 5970 $"
__date__      = "$Date: 2005-07-12 16:27:25 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.packs.chandler.Types import LocalizableString
import i18nmanager

#We temporarily assign _() to return the value it is passed.
# till  LocalizableString is put in place in the Chandler code base

def gettextStandin(text):
    return text

import __builtin__
__builtin__.__dict__['_'] = gettextStandin

I18nManager = i18nmanager.I18nManager()


def MessageFactory(domain):
    def createLocalizableString(ustring):
        return LocalizableString(domain, ustring)
    return createLocalizableString

def OSAFMessageFactory(ustring):
    return MessageFactory(i18nmanager.OSAF_DOMAIN)(ustring)

#XXX: is this needed?
def MessageFactoryUnicode(domain):
    def createUnicode(ustring):
        return LocalizableString(domain, ustring).toUnicode()
    return createUnicode

#XXX: is this needed?
def OSAFMessageFactoryUnicode(ustring):
    return MessageFactoryUnicode(i18nmanager.OSAF_DOMAIN)(ustring)



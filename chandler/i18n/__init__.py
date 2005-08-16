__revision__  = "$Revision: 5970 $"
__date__      = "$Date: 2005-07-12 16:27:25 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.packs.chandler.Types import LocalizableString
from types import ListType, UnicodeType
import i18nmanager

I18nManager = i18nmanager.I18nManager()

def MessageFactory(domain):
    def createLocalizableString(ustring):
        return LocalizableString(domain, ustring)
    return createLocalizableString

def MessageFactoryUnicode(domain):
    def createUnicode(ustring):
        return LocalizableString(domain, ustring).toUnicode()
    return createUnicode

def OSAFMessageFactory(ustring):
    return MessageFactory(i18nmanager.OSAF_DOMAIN)(ustring)

def OSAFMessageFactoryUnicode(ustring):
    return MessageFactoryUnicode(i18nmanager.OSAF_DOMAIN)(ustring)



__revision__  = "$Revision: 5970 $"
__date__      = "$Date: 2005-07-12 16:27:25 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from i18nmanager import *

__all__ = ["I18nException", "MessageFactory", "OSAFMessageFactory",
           "discoverLocaleSet", "setLocaleSet", "getLocaleSet",
           "getImage", "getHTML", "getAudio", "getResource"]


class I18nException(Exception):
    pass

"""I18nManager instance used by the internationalization API.
   It is not exposed to external developers but can be referenced
   for advanced operations"""
_I18nManager = i18nmanager.I18nManager()

"""Expose the I18nManager instance methods"""
#XXX: May not want to expose this. Only Chandler core code should
#     leverage this method
discoverLocaleSet = _I18nManager.discoverLocaleSet
#XXX: May not want to expose this. Only Chandler core code should
#     leverage this method
setLocaleSet = _I18nManager.setLocaleSet
getLocaleSet = _I18nManager.getLocaleSet
getImage = _I18nManager.getImage
getHTML = _I18nManager.getHTML
getAudio = _I18nManager.getAudio
getResource = _I18nManager.getResource



def MessageFactory(domain):
    def getTranslation(defaultText):
        #XXX This will raise UnicodeDecodeError on failure
        #    which is ok cause the errror will alert the developer 
        #    to the error. I.e. they did not pass in an ascii or unicode string
        defaultText = unicode(defaultText)

        return _I18nManager.translate(domain, defaultText)
    return getTranslation

def OSAFMessageFactory(defaultText):
    return MessageFactory(OSAF_DOMAIN)(defaultText)



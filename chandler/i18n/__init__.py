__revision__  = "$Revision: 5970 $"
__date__      = "$Date: 2005-07-12 16:27:25 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import i18nmanager

__all__ = ["I18nException", "MessageFactory", "OSAFMessageFactory", "I18nManager"]


class I18nException(Exception):
    pass

"""Expose the I18nManager instance"""
I18nManager = i18nmanager.I18nManager()

"""Expose the I18nManager instance methods"""
discoverLocaleSet = I18nManager.discoverLocaleSet
setLocaleSet = I18nManager.setLocaleSet
getLocaleSet = I18nManager.getLocaleSet
translate = I18nManager.translate
getImage = I18nManager.getImage
getHTML = I18nManager.getHTML
getAudio = I18nManager.getAudio
getResource = I18nManager.getResource



def MessageFactory(domain):
    def getTranslation(defaultText):
        #XXX This will raise UnicodeDecodeError on failure
        #    which is ok cause the errror will alert the developer 
        #    to the error. I.e. they did not pass in an ascii string
        defaultText = unicode(defaultText)

        return translate(domain, defaultText)
    return getTranslation

def OSAFMessageFactory(defaultText):
    return MessageFactory(i18nmanager.OSAF_DOMAIN)(defaultText)



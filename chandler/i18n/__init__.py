__revision__  = "$Revision: 5970 $"
__date__      = "$Date: 2005-07-12 16:27:25 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from i18nmanager import *
import sys

__all__ = ["I18nException", "MessageFactory", "OSAFMessageFactory",
           "discoverLocaleSet", "setLocaleSet", "getLocaleSet",
           "getImage", "getHTML", "getAudio", "getResource", "OSAF_DOMAIN",
           "DEFAULT_LOCALE_SET"]


OSAF_DOMAIN = "osaf"
DEFAULT_LOCALE_SET = ["en_US", "en"]


"""I18nManager instance used by the internationalization API.
   It is not exposed to external developers but can be referenced
   for advanced operations"""
_I18nManager = i18nmanager.I18nManager(OSAF_DOMAIN, DEFAULT_LOCALE_SET)


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
    """
    Chandler translation API. A MessageFactory is leveraged per unique domain
    to access the localiztion files which are in gettext .mo format.

    A unique domain can be created per parcel or for a grouping of parcels.
    A domain is namespace under which translation strings reside.

    The default domain for Chandler core is "osaf" and can be accessed using the
    OSAFMessageFactory.

    A MessageFactory example:
    >>> from i18n import MessageFactory
    >>> _ = MessageFactory("mydomain")
    >>> translatedString = _(u"Some text for translation")

    An alternate example which does not use the _ method shortcut.
    It should be noted that the gettext api looks for _() to find translation
    strings:

    >>> from i18n import MessageFactory
    >>> m = MessageFactory("mydomain")
    >>> translatedString = m.getTranslation(u"Some text for translation")


    @type domain: ASCII str
    @param domain: unique ASCII domain name

    @rtype: function
    @return: A MessageFactory.getTranslation function instance
    """

    def getTranslation(defaultText):
        """
        Performs a translation lookup using the defaultText as the key.
        Translation files are stored in the gettext .mo format and
        cached on startup. The defaultText key is looked up for
        each locale in the curent locale set until a match is found.
        If no match is found the defaultText is returned as the value.

        @type defaultText: unicode
        @param defaultText: the unicode default key in english

        @rtype: unicode
        @return: The unicode localized string for key defaultText or the
                 defaultText if no match found
        """

        #XXX This will raise UnicodeDecodeError on failure
        #    which is ok cause the errror will alert the developer 
        #    to the error. I.e. they did not pass in an ascii or unicode string

        defaultText = unicode(defaultText)
        return _I18nManager.translate(domain, defaultText)

    return getTranslation

def OSAFMessageFactory(defaultText):
    """
    The translation message factory for Chandler Core.
    The OSAFMessageFactory is intended as shortcut to allow easy access to translations 
    in the "osaf" domain.

    An OSAFMessageFactory example:
    >>> from i18n import OSAFMessageFactory as _
    >>> translatedString = _(u"Some text for translation")

    The functionality provided by the OSAFMessageFactory can be accessed using a MessageFactory.
    Again the OSAFMessageFactory is provided as a shortcut

    >>> from i18n import MessageFactory
    >>> import i18n
    >>> _ = MessageFactory(i18n.OSAF_DOMAIN)
    >>> translatedString = _(u"Some text for translation")

    @type defaultText: unicode
    @param defaultText: the unicode default key in english

    @rtype: unicode
    @return: The unicode localized string for key defaultText or the
             defaultText if no match found
    """

    return MessageFactory(OSAF_DOMAIN)(defaultText)


class I18nException(Exception):
    pass

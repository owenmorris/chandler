#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


from i18nmanager import *
import sys

__all__ = ["I18nException", "MessageFactory", "OSAFMessageFactory",
            "wxMessageFactory", "getLocaleSet", "getImage", "getHTML",
            "getAudio", "getResource", "OSAF_DOMAIN"]


OSAF_DOMAIN = "osaf"


"""I18nManager instance used by the internationalization API.
   It is not exposed to external developers but can be referenced
   for advanced operations"""
_I18nManager = i18nmanager.I18nManager(OSAF_DOMAIN)


"""Expose the I18nManager instance methods"""
getLocaleSet = _I18nManager.getLocaleSet
getImage = _I18nManager.getImage
getHTML = _I18nManager.getHTML
getAudio = _I18nManager.getAudio
getResource = _I18nManager.getResource


def MessageFactory(domain):
    """
        Chandler translation API. A MessageFactory is leveraged per
        unique domain to access the localiztion files 
        which are in gettext .mo format.

        A unique domain can be created per parcel or for a
        grouping of parcels.

        A domain is namespace under which translation strings reside.

       The default domain for Chandler core is "osaf" and 
       can be accessed using the OSAFMessageFactory.

        A MessageFactory example:
        >>> from i18n import MessageFactory
        >>> _ = MessageFactory("mydomain")
        >>> translatedString = _(u"Some text for translation")

        An alternate example which does not use the _ method shortcut.
        It should be noted that the gettext api looks for _() to find
        translation strings:

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

            @type defaultText: unicode or ascii
            @param defaultText: the unicode or ascii default key

            @rtype: unicode
            @return: The unicode localized string for key defaultText or the
                 defaultText if no match found
        """

        #XXX This will raise UnicodeDecodeError on failure
        #    which is ok cause it will alert the developer 
        #    that he or she  did not pass in an ascii or
        #  unicode string

        defaultText = unicode(defaultText)
        return _I18nManager.translate(domain, defaultText)

    return getTranslation

def wxMessageFactory(defaultText):
    """
        The translation message factory for WxWidgets.
        The wxMessageFactory is intended as shortcut to allow easy
        access to translations in the "wxstd" domain.

        The domain must have been loaded by the I18nManager 
        in order to access the translations. Otherwise an
        i18n.I18nException will be raised.


        A wxMessageFactory example:
        >>> from i18n import wxMessageFactory as w
        >>> translatedString = w("Cancel")

        @type defaultText: unicode or ascii
        @param defaultText: the unicode or ascii default key

        @rtype: unicode
        @return: The unicode localized string for key defaultText or the
                 defaultText if no match found
    """


    #XXX This will raise UnicodeDecodeError on failure
    #    which is ok cause it will alert the developer 
    #    that he or she  did not pass in an ascii or
    #  unicode string
    return _I18nManager.wxTranslate(unicode(defaultText))


def OSAFMessageFactory(defaultText):
    """
        The translation message factory for Chandler Core.
        The OSAFMessageFactory is intended as shortcut to allow easy
        access to translations in the "osaf" domain.

        An OSAFMessageFactory example:
        >>> from i18n import OSAFMessageFactory as _
        >>> translatedString = _(u"Some text for translation")

        The functionality provided by the OSAFMessageFactory can 
        be accessed using a MessageFactory.  Again the OSAFMessageFactory 
        is provided as a shortcut

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

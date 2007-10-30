#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


from i18nmanager import I18nManager, I18nException
from types import UnicodeType, StringType

__all__ = ["MessageFactory", "ChandlerMessageFactory", "NoTranslationMessageFactory",
           "SafeTranslationMessageFactory", "ChandlerSafeTranslationMessageFactory",
           "wxMessageFactory", "getLocale", "getLocaleSet", "getOSLocale",
           "getAvailableChandlerLocales", "getImage", "getHTML", "Message"]

CHANDLER_PROJECT = u"Chandler"
DEFAULT_CATALOG  = u"gettext.catalog"
DEFAULT_IMAGE    = u"img.resources"
DEFAULT_HTML     = u"html.resources"

"""
I18nManager instance used by the internationalization API.
It is not exposed to external developers but can be referenced
for advanced operations
"""
_I18nManager = I18nManager(CHANDLER_PROJECT, DEFAULT_CATALOG,
                           DEFAULT_IMAGE, DEFAULT_HTML)
"""
Expose the I18nManager instance methods
"""
getLocaleSet = _I18nManager.getLocaleSet
getImage = _I18nManager.getImage
getHTML = _I18nManager.getHTML
getOSLocale = _I18nManager.discoverLocaleSet

class Message(unicode):
    __slots__ = ('msgid', 'project', 'catalog_name')

    def __new__(cls, project, catalog_name, msgid, msgstr):
        self = unicode.__new__(cls, msgstr)
        self.project = project
        self.catalog_name = catalog_name
        self.msgid = msgid

        return self

def getAvailableChandlerLocales():
    """
       Return the list of translation egg locales
       registered for Chandler
    """
    return _I18nManager.getAvailableLocales(CHANDLER_PROJECT)

def getLocale():
   """
   Returns the primary Chandler locale.
   """
   return getLocaleSet()[0]


def NoTranslationMessageFactory(msgid):
    """
    The c{NoTranslationMessageFactory} method
    returns the msgid passed
    in its original form. No translation is
    performed.

    The c{NoTranslationMessageFactory} should be used
    as a means of ensuring English keys are
    parsed and rendered to a .pot when
    the translation is done by other means.
    """
    return msgid


def MessageFactory(project, catalog_name=DEFAULT_CATALOG):
    """
    Chandler translation API. A c{MessageFactory} is leveraged per
    unique project to access the localization files
    which are in gettext .mo format.

    A unique project can be created per parcel or for a
    grouping of parcels.

    A project is namespace under which translation strings reside.

    A c{MessageFactory} example:

    >>> from i18n import MessageFactory
    >>> _ = MessageFactory("myproject")
    >>> translatedString = _(u"Some text for translation")

    @param project: A project is a root namespace under which
                    resources and localizations exist.

                    A project name matches an egg name.
                    An egg's info file can contain resource
                    and localizations for more than one project.

                    The project name must be either an ASCII
                    c{str} or c{unicode}.

     @type project: ASCII c{str} or c{unicode}

    @rtype: function
    @return: A MessageFactory.getText function instance
    """

    def getText(msgid):
        """
        Performs a translation lookup using the msgid as the key.
        Translation files are stored in the gettext .mo format and
        cached on startup. The msgid key is looked up for
        each locale in the curent locale set until a match is found.
        If no match is found the msgid is returned as the value.

        @param msgid: the unicode or ascii default key
        @type msgid: c{unicode} or ASCII c{str}

        @rtype: c{Message} a unicode sub-class
        @return: c{Message} object sub-class of unicode containing the
                localization or msgid if no localization found.
        """

        if type(msgid) == StringType:
            msgid = unicode(msgid)

        assert(type(msgid) == UnicodeType)

        msgstr = _I18nManager.getText(project, catalog_name, msgid)

        return Message(project, catalog_name, msgid, msgstr)

    return getText

def wxMessageFactory(msgid):
    """
    The translation message factory for WxWidgets.
    The wxMessageFactory is intended as a shortcut to allow easy
    access to translations in the "wxstd" project.

    The "wxstd" project must have been loaded by the c{I18nManager}
    in order to access the translations. Otherwise the
    msgid will be returned.

    A c{wxMessageFactory} example:

    >>> from i18n import wxMessageFactory as w
    >>> translatedString = w("Cancel")

    @param msgid: the unicode or ASCII default key
    @type msgid: ASCII c{str} or c{unicode}

    @rtype: unicode
    @return: The unicode localized string for key msgid or the
             msgid if no match found
    """
    if type(msgid) == StringType:
        msgid = unicode(msgid)

    assert(type(msgid) == UnicodeType)

    return _I18nManager.wxTranslate(msgid)


def SafeTranslationMessageFactory(project, catalog_name=DEFAULT_CATALOG):
    """
    A c{SafeTranslationMessageFactory} is leveraged per
    unique project to access the localization files
    which are in gettext .mo format.

    A unique project can be created per parcel or for a
    grouping of parcels.

    A project is namespace under which translation strings reside.

    Unlike the c{MessageFactory} and c{ChandlerMessageFactory}
    which will raise an Exception if called before i18n is initialized,
    A safe translation will return the default text passed in cases where
    i18n initialization has failed or has not been called.

    This method should be used *only* in the cases where
    a string must be displayed whether i18n has
    successfully initialized or not.

    A c{SafeTranslationMessageFactory} example:

    >>> from i18n import SafeTranslationMessageFactory
    >>> _ = SafeTranslationMessageFactory("myproject")
    >>> translatedString = _(u"Some text for translation")

    @param project: A project is a root namespace under which
                    resources and localizations exist.

                    A project name matches an egg name.
                    An egg's info file can contain resource
                    and localizations for more than one project.

                    The project name must be either an ASCII
                    c{str} or c{unicode}.

     @type project: ASCII c{str} or c{unicode}

    @rtype: function
    @return: A SafeTranslationMessageFactory.getText function instance
    """

    mf =  MessageFactory(project, catalog_name)

    def getText(msgid):
        """
        Performs a translation lookup using the msgid as the key.
        Translation files are stored in the gettext .mo format and
        cached on startup. The msgid key is looked up for
        each locale in the curent locale set until a match is found.
        If no match is found the msgid is returned as the value.

        @param msgid: the unicode or ascii default key
        @type msgid: c{unicode} or ASCII c{str}

        @rtype: c{Message} a unicode sub-class
        @return: c{Message} object sub-class of unicode containing the
                localization or msgid if no localization found.
        """
        if type(msgid) == StringType:
            msgid = unicode(msgid)

        assert(type(msgid) == UnicodeType)

        try:
            return mf(msgid)
        except:
            return msgid

    return getText


def ChandlerMessageFactory(msgid):
    """
    The translation message factory for Chandler.
    The ChandlerMessageFactory is intended as shortcut to allow easy
    access to translations in the "Chandler" project.

    A ChandlerMessageFactory example:
    >>> from i18n import ChandlerMessageFactory as _
    >>> translatedString = _(u"Some text for translation")

    The functionality provided by the ChandlerMessageFactory can
    be accessed using a MessageFactory.  Again the ChandlerMessageFactory
    is provided as a shortcut

    >>> from i18n import MessageFactory
    >>> import i18n
    >>> _ = MessageFactory(CHANDLER_PROJECT, DEFAULT_CATALOG)
    >>> translatedString = _(u"Some text for translation")

    @param msgid: the unicode or ASCII default key
    @type msgid: ASCII c{str} or c{unicode}

    @rtype: c{Message} a unicode sub-class
    @return: c{Message} object sub-class of unicode containing the
            localization or msgid if no localization found.
    """
    return MessageFactory(CHANDLER_PROJECT, DEFAULT_CATALOG)(msgid)


def ChandlerSafeTranslationMessageFactory(msgid):
    """
    A safe translation message factory for Chandler.
    The c{ChandlerSafeTranslationMessageFactory} is intended as
    shortcut to allow easy access to safe translations in the "Chandler" project.

    Unlike the c{MessageFactory} and c{ChandlerMessageFactory} 
    which will raise an Exception if called before i18n is initialized,
    A safe translation will return the default text passed in cases where 
    i18n initialization has failed or has not been called.

    This method should be used *only* in the cases where
    a string must be displayed whether i18n has
    successfully initialized or not.

    A c{ChandlerSafeTranslationMessageFactory} example:

    >>> from i18n import ChandlerSafeTranslationMessageFactory as _
    >>> translatedString = _(u"Some text for translation")

    The functionality provided by the c{ChandlerSafeTranslationMessageFactory} can
    be accessed using a c{SafeTranslationMessageFactory}.  Again the
    c{ChandlerSafeTranslationMessageFactory} is provided as a shortcut.

    >>> from i18n import SafeTranslationMessageFactory
    >>> _ = SafeTranslationMessageFactory(CHANDLER_PROJECT, DEFAULT_CATALOG)
    >>> translatedString = _(u"Some text for translation")

    @param msgid: the unicode or ASCII default key
    @type msgid: ASCII c{str} or c{unicode}

    @rtype: c{Message} a unicode sub-class
    @return: c{Message} object sub-class of unicode containing the
             localization or msgid if no localization found.
    """
    return SafeTranslationMessageFactory(CHANDLER_PROJECT, DEFAULT_CATALOG)(msgid)

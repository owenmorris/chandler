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


from i18nmanager import I18nManager, I18nException
from types import UnicodeType, StringType

__all__ = ["MessageFactory", "ChandlerMessageFactory",
           "wxMessageFactory", "getLocaleSet", "getImage", "getHTML"]

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

def MessageFactory(project, catalog_name=DEFAULT_CATALOG):
    """
    Chandler translation API. A MessageFactory is leveraged per
    unique project to access the localiztion files
    which are in gettext .mo format.

    A unique project can be created per parcel or for a
    grouping of parcels.

    A project is namespace under which translation strings reside.

    A MessageFactory example:
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

    def getText(defaultText):
        """
        Performs a translation lookup using the defaultText as the key.
        Translation files are stored in the gettext .mo format and
        cached on startup. The defaultText key is looked up for
        each locale in the curent locale set until a match is found.
        If no match is found the defaultText is returned as the value.

        @param defaultText: the unicode or ascii default key
        @type defaultText: c{unicode} or ASCII c{str}

        @rtype: unicode
        @return: The unicode localized string for key defaultText or the
                 defaultText if no match found
        """

        if type(defaultText) == StringType:
            defaultText = unicode(defaultText)

        assert(type(defaultText) == UnicodeType)

        return _I18nManager.getText(project, catalog_name, defaultText)

    return getText

def wxMessageFactory(defaultText):
    """
    The translation message factory for WxWidgets.
    The wxMessageFactory is intended as shortcut to allow easy
    access to translations in the "wxstd" project.

    The project must have been loaded by the I18nManager
    in order to access the translations. Otherwise an
    I18nException will be raised.


    A wxMessageFactory example:
    >>> from i18n import wxMessageFactory as w
    >>> translatedString = w("Cancel")

    @param defaultText: the unicode or ASCII default key
    @type defaultText: ASCII c{str} or c{unicode}

    @rtype: unicode
    @return: The unicode localized string for key defaultText or the
             defaultText if no match found
    """
    if type(defaultText) == StringType:
        defaultText = unicode(defaultText)

    assert(type(defaultText) == UnicodeType)

    return _I18nManager.wxTranslate(defaultText)


def ChandlerMessageFactory(defaultText):
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

    @param defaultText: the unicode or ASCII default key
    @type defaultText: ASCII c{str} or c{unicode}

    @rtype: unicode
    @return: The unicode localized string for key defaultText or the
             defaultText if no match found
    """
    return MessageFactory(CHANDLER_PROJECT, DEFAULT_CATALOG)(defaultText)

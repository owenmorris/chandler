
__revision__  = "$Revision: 5970 $"
__date__      = "$Date: 2005-07-12 16:27:25 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from types import UnicodeType, StringType

"""
Notes:
1. Should Exception be i18nException or RepositoryException
"""

class LocalizableString(object):
    __slots__ = ['_domain', '_defaultText', "_args"]

    def __init__(self, domain, defaultText):
        assert isinstance(domain, StringType)
        assert isinstance(defaultText, UnicodeType)

        super(LocalizableString, self).__init__()

        self._domain = domain
        self._defaultText = defaultText
        """Non-persisted value"""
        self._args = None


    def __repr__(self):
        return "LocalizableString(%r, %r)" % (self._domain, self._defaultText)

    def __mod__(self, args):
       #xXX: what restrictions to put on args?
        if __debug__:
            """If we are running in debug mode test the args against the
               key to make sure correct number of args passed in. This
               may still cause a failure in translation if the localized
               text arguments do not match the default arguments"""

            self._defaultText % args

        self._args = args

        return self

    def __str__(self):
        from i18n import I18nException
        raise I18nException("String casts are not supported. \
                             Use the encode method to convert unicode to bytes")

    def __unicode__(self):
        from i18n import I18nManager
        args = self._args

        #Clear the args after returning translation
        self._args = None

        return I18nManager.translate(self._domain, self._defaultText, args)

    def encode(self, charset):
        return self.__unicode__().encode(charset)

    def toUnicode(self):
        return self.__unicode__()


from repository.schema.Types import Struct
from repository.schema.Alias import Alias

class LocalizableStringType(Struct):
    def makeValue(self, data):
        return LocalizableString(data)

class Text(Alias):
    def makeValue(self, data):
        return LocalizableString(data)



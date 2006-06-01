import unicodedata

__all__ = ["addUnicodeWrapper", "uw"]


I18N_SEED = [
    #XXX: Some of these characters do not render properly in a 
    #     Windows UI.
    u'\u00C5', #LATIN CAPITAL LETTER A WITH RING ABOVE
    u'\u00FC', #LATIN SMALL LETTER U WITH DIAERESIS
    u'\u0414', #CYRILLIC CAPITAL LETTER DE
    u'\u062B', #ARABIC LETTER THEH
    u'\u0E12', #THAI CHARACTER THO PHUTHAO
    u'\u30C4', #KATAKANA LETTER TU
    u'\u0439', #CYRILLIC SMALL LETTER SHORT I
    u'\u03b4', #GREEK SMALL LETTER DELTA
    u'\u8fd1', #CJK UNIFIED IDEOGRAPH-8FD1
    u'\u85e4', #CJK UNIFIED IDEOGRAPH-85E4
    u'\u6df3', #CJK UNIFIED IDEOGRAPH-6DF3
    u'\u4e5f', #CJK UNIFIED IDEOGRAPH-4E5F
    u'\u65b0', #CJK UNIFIED IDEOGRAPH-65B0
    u'\u30c3', #KATAKANA LETTER SMALL TU
    u'\u30c8', #KATAKANA LETTER TO
    u'\u30b3', #KATAKANA LETTER KO
    u'\u30df', #KATAKANA LETTER MI
    u'\u30e5', #KATAKANA LETTER SMALL YU
    u'\u30cb', #KATAKANA LETTER NI
    u'\u30c6', #KATAKANA LETTER TE
    u'\u30a3', #KATAKANA LETTER SMALL I
    u'\u8ad6', #CJK UNIFIED IDEOGRAPH-8AD6
]

I18N_SEED_SIZE = len(I18N_SEED)

def printUCs():
    """ Used internally for debugging """
    for i in xrange(I18N_SEED_SIZE):
        uc = I18N_SEED[i]
        print "char: %s ord: %s name: %s" % \
               (uc.encode("utf8"), ord(uc), unicodedata.name(uc))
    
def getUC(seed):
    return I18N_SEED[ord(seed) % I18N_SEED_SIZE]

#XXX Not thread safe
def addUnicodeWrapper(defaultText):
    """
        This method is used for testing and append unicode characters 
        to the first and last positions in the defaultText string.

        The unicode character for the first position is chosen by moding the 
        ord of the first character in the defaultString with the size of the 
        18n seed unicode character array. The unicode character in the last position
        is always u'\u062B', ARABIC LETTER THEH

        @type defaultText: unicode or ascii str
        @param defaultText: the text to wrap with unicode chars

        @rtype: unicode
        @return: The original defaultText plus unicode 
                 chars wrapping it. 
    """

    if defaultText is None or len(defaultText) == 0:
        return defaultText

    #\u0628 is ARABIC LETTER THEH
    return u"%s%s%s" % (getUC(defaultText[0]), defaultText, u'\u062B')

# Shortcut for calling addUnicodeWrapper. Used in the same manner as gettext and
# OSAF MessageFactories use the _(). instead of typing
# addUnicodeWrapper("text") one can use the short cut uw("text").
uw = addUnicodeWrapper

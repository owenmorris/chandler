import random

__all__ = ["AddUnicodeWrapper", "uw"]


# The unicode characters chosen at random as part of a 
# getRandUnicodeChar method call
I18N_SEED = [
    u'\u00C5', #Nordic
    u'\u00FC', #German
    u'\u0414', #Cyrillic
    u'\u062B', #"Arabic"
    u'\u0E12', #Thai
    u'\u30C4', #Japanese
    u'\u0439',
    u'\u03b4',
    u'\u8fd1',
    u'\u85e4',
    u'\u6df3',
    u'\u4e5f',
    u'\u306e',
    u'\u65b0',
    u'\u30cd',
    u'\u30c3',
    u'\u30c8',
    u'\u30b3',
    u'\u30df',
    u'\u30e5',
    u'\u30cb',
    u'\u30c6',
    u'\u30a3',
    u'\u8ad6',
]

I18N_SEED_SIZE = len(I18N_SEED)

I18N_SEED_CACHE = {}

def getRandUnicodeChar():
    return I18N_SEED[random.randrange(I18N_SEED_SIZE)]

#XXX Not thread safe
def addUnicodeWrapper(defaultText):
    """
        This method is used for testing and adds unicode characters 
        to the first and last positions in the defaultText string.

        The unicode characters are chosen at random from an array of
        unicode characters. However, once a value is returned from 
        addUnicodeWrapper it is cached. The addUnicodeWrapper method will always
        return the same wrapped value during a Python run. The values
        returned will differ however from run to run. 

        Since most tests use comparison as a means of validation, the caching 
        mechanism ensures that the comparisons will be the same.

        @type defaultText: unicode or ascii str
        @param defaultText: the text to wrap with unicode chars

        @rtype: unicode
        @return: The original defaultText plus random unicode 
                 chars wrapping it. 
    """
    if I18N_SEED_CACHE.has_key(defaultText):
        return I18N_SEED_CACHE[defaultText]

    u = u"%s%s%s"% (getRandUnicodeChar(), defaultText, getRandUnicodeChar())

    I18N_SEED_CACHE[defaultText] = u
    return u

# Shortcut for calling addUnicodeWrapper. Used in the same manner as gettext and
# OSAF MessageFactories use the _(). instead of typing
# addUnicodeWrapper("text") one can use the short cut uw("text").
uw = addUnicodeWrapper

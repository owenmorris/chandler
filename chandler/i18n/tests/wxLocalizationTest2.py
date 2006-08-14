import i18n
import sys
from i18n import wxMessageFactory as w

i18nMan = i18n._I18nManager


def translate():
    print "Using Locale: ", i18n.getLocaleSet()[0]
    print "Cancel: ", w("Cancel").encode("utf8")
    print "Quit: ", w("&Quit").encode("utf8")


i18nMan.initialize('fr_CA')
translate()
i18nMan.setLocaleSet('es_UY')
translate()


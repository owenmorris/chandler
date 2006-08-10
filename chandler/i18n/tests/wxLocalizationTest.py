from application import Utility
import i18n
import sys, os
from i18n import wxMessageFactory as w

"""
Command line utility to confirm that wx localization files are loaded
   And options locale can be specified on the command line: If no locale is
   passed the System default locale is used:

   Load the French wx translations:
   ===================================
   ./release/RunPython i18n/tests/wxLocalizationTest.py fr


   Load the System default  wx translations:
   ===================================
   ./release/RunPython i18n/tests/wxLocalizationTest.py
"""
i18nMan = i18n._I18nManager

if len(sys.argv) > 1:
    i18nMan.initialize(sys.argv[1])
else:
    i18nMan.initialize(None)

print "Using Locale: ", i18n.getLocaleSet()[0]

print "Cancel: ", w("Cancel").encode("utf8")
print "Quit: ", w("&Quit").encode("utf8")



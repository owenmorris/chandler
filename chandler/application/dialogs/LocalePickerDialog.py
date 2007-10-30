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

import wx
from i18n import getAvailableChandlerLocales, getLocale
from i18n.i18nmanager import hasWxLocale
from PyICU import Locale
from i18n import ChandlerMessageFactory as _
from egg_translations import stripCountryCode, hasCountryCode
from application import Globals, Utility
import sys

DIALOG_WIDTH = 350

def showLocalePickerDialog():
    win = LocalePickerDialog()

    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
        # Get the new locale and if it differs from
        # current locale restart Chandler
        currentLocale = getLocale()
        newLocale = win.GetValue()

        if newLocale != currentLocale:
            prefs = Utility.loadPrefs(Globals.options)

            if 'options' not in prefs:
                prefs['options'] = {}

            prefs['options']['locale'] = newLocale
            prefs.write()

            # The locale needs to be passed since
            # restart preserves the command line
            # options from the previous startup.
            # If the previous startup contained
            # a locale command line flag it
            # will override the value for the locale
            # just added to the prefs file and
            # Chandler will not switch the locale
            # as expected.
            wx.GetApp().restart(locale=newLocale)

    win.Destroy()

class LocalePickerDialog(wx.Dialog):
    def __init__(self):
        super(LocalePickerDialog, self).__init__(wx.GetApp().mainFrame, -1,
                                                u"", style=wx.DEFAULT_DIALOG_STYLE)
        self._locales = {}

        localeCodes = getAvailableChandlerLocales()
        icuLocales = Locale.getAvailableLocales()
        icuLocaleCodes = icuLocales.keys()
        langCodeAdded = {}
        linux = sys.platform.startswith('linux')

        for localeCode in localeCodes:
            langCode = stripCountryCode(localeCode)

            if linux and not hasWxLocale(langCode):
                # Not all WxPython translations are
                # installed by default on English
                # versions of Linux. Thus even
                # though there is a translation
                # egg available for Chandler, wx
                # will raise an error on Chandler
                # start up
                continue

            if hasCountryCode(localeCode) and not \
               langCode in localeCodes:
                    # There is no translation egg available for
                    # the langCode (fallback). In this case, country variations
                    # can not be made available to the user. This will
                    # be rare if ever happen that say a "fr_CA" egg is
                    # registered with Chandler but not an "fr" egg.
                    self._locales[Locale(localeCode).getDisplayName()] = localeCode
                    continue

            if not langCodeAdded.has_key(langCode):
                added = False

                for icuLocale in icuLocaleCodes:
                    if icuLocale.startswith(langCode):
                        self._locales[icuLocales[icuLocale].getDisplayName()] = icuLocale
                        added = True
                if added:
                    langCodeAdded[langCode] = True

        currentLocale = getLocale()
        currentLocaleName = Locale(currentLocale).getDisplayName()

        if currentLocale not in localeCodes:
            # Add the current locale to the locale selection list.
            # This case occurs when a user manual specifies a locale
            # on the command line or via prefs that does not have
            # a translation egg installed.
            self._locales[currentLocaleName] = currentLocale

        choices = self._locales.keys()
        choices.sort()


        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, _(u"Please select a language:"), size=(DIALOG_WIDTH,-1))
        label.Wrap(DIALOG_WIDTH)

        sizer.Add(label, 0, wx.ALIGN_CENTER|wx.ALL, 10)

        self._localeChoices = wx.Choice(self, -1, choices=choices, size=(DIALOG_WIDTH-70, -1))

        sizer.Add(self._localeChoices, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 10)

        pos = self._localeChoices.FindString(currentLocaleName)

        if pos != wx.NOT_FOUND:
            self._localeChoices.SetSelection(pos)

        sizer.AddSpacer(10, 0)

        bsizer = wx.BoxSizer(wx.HORIZONTAL)

        # Load the wx.ICON_EXCLAMATION icon
        bmp = wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_MESSAGE_BOX, (32,32))
        icon = wx.StaticBitmap(self, -1, bmp)
        bsizer.Add(icon, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)

        note = wx.StaticText(self, -1,
                           _(u"Switching languages will cause Chandler to automatically restart."))

        note.Wrap(DIALOG_WIDTH)

        bsizer.Add(note, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)
        sizer.Add(bsizer)

        sizer.AddSpacer(5, 0)

        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL)
        box.Add(btn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 10)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def GetValue(self):
        localeName = self._localeChoices.GetString(self._localeChoices.GetSelection())
        return self._locales[localeName]

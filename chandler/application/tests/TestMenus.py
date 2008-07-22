#   Copyright (c) 2008 Open Source Applications Foundation
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

import sys
import unittest
import itertools
from application import schema, Globals, Utility
from chandlerdb.persistence.RepositoryView import NullRepositoryView

Globals.chandlerDirectory = Utility.locateChandlerDirectory()
Globals.options = Utility.initOptions()

class MenuTestCase(unittest.TestCase):
    """
    Tests of consistent mnemonics/shortcuts in Chandler's menus.
    """
    view = None
    
    def setUp(self):
        # This setup is needed because we'd like to be able to use
        # --locale on the command line to test a given locale. So,
        # basically the code below is copy-and-pasted out of Utility.py
        # to make sure that everything gets initialized in the right
        # order.
        needInit = (self.view is None)
        
        # We always store a list of all failures, so that we can report them
        # all rather than fail on the first.
        self.failures = []

        if needInit:
            Utility.initLogging(Globals.options)
            type(self).view = NullRepositoryView()
            
            parcelPath = Utility.initParcelEnv(Globals.options, 
                                               Globals.chandlerDirectory)
            pluginEnv, pluginEggs = Utility.initPluginEnv(Globals.options,
                                                  Globals.options.pluginPath)
                        
            Utility.initI18n(Globals.options)

            Utility.initParcels(Globals.options, self.view, parcelPath)
            Utility.initPlugins(Globals.options, self.view, pluginEnv,
                                pluginEggs)
        # We don't want to import these globally, because they will
        # trigger parcel loading, and that will cause i18n to be set
        # up before the above call to initI18n, which will mean --locale
        # won't work on the command line. So, instead, we stash these
        # in instance variables.
        self.Menu = schema.importString('osaf.framework.blocks.Menu')
        self.MenuItem = schema.importString('osaf.framework.blocks.MenuItem')


    def checkFailures(self):
        if self.failures:
            sys.stderr.write("\n--------------------------------\n")
            for f in self.failures:
                sys.stderr.write("\n%s\n" % (f.encode('UTF-8'),))
            self.fail("%s failure(s)" % (len(self.failures),))


    def _appendFailure(self, msg, *args):
        # Method used to append an failure to self.failures.
        # msg is the usual python-style format string, while we process
        # some args specially:
        #
        # - Any Menu/MenuItem is pretty-printed, in the form:
        #
        #  Root >> Sub&menu >> &Item
        #
        # - A 2-element tuple is a hack used for marking a "toggleTitle"
        #   menu item title (i.e. an alternative to the menu title when some
        #   state has changed) used when reporting mnemonic problems. We'll
        # print out a [toggleTitle] in the error message here to clarify
        # whhere the problem lies.
        blockClass = schema.importString('osaf.framework.blocks.Block.Block')
        def _itemPath(obj):
            if isinstance(obj, tuple):
                obj, title = obj

                yield "%s[toggle]" % (title,)
                obj = obj.parentBlock

            while obj is not None:
                try:
                    yield obj.getAttributeValue('title')
                except AttributeError:
                    if not isinstance(obj, blockClass):
                        yield unicode(obj)
                obj = getattr(obj, 'parentBlock', None)

        prettyArgs = tuple(" >> ".join(reversed(tuple(_itemPath(arg))))
                             for arg in args)
        self.failures.append(msg % prettyArgs)

    def testMnemonics(self):
        for menu in self.Menu.iterItems(self.view):
            # We want to make sure that all non-separator menu items in each
            # menu have a unique mnemonic. In addition, if the menu item has
            # a toggleTitle, we want to make sure that that item has a unique
            # mnemonic w.r.t. other menu items (it's fine to have the same
            # mnemonic as the regular title).
            #
            # So, we build up a dictionary, mnemonicToItems, that has lowercase
            # mnemonic as key, and a list of all menu items for each value. Once
            # we're done, we can check that each value has exactly one item, or
            # else we have duplicates. 
            mnemonicToItems = {}
            
            def extractMnemonic(item, title):
                if not title:
                    return None
                mIndex = title.find("&") + 1
                if mIndex in (0, len(title)):
                    return None
                else:
                    return title[mIndex].lower()

            def updateDict(m, item):
                value = mnemonicToItems.setdefault(m, [])
                value.append(item)
            
            for subitem in menu.childBlocks:
                if subitem.menuItemKind != 'Separator':
                    mnemonic = extractMnemonic(subitem, subitem.title)
                    
                    if mnemonic is None:
                        self._appendFailure("Missing mnemonic for item %s", subitem)
                    else:
                        updateDict(mnemonic, subitem)
                        
                        toggleTitle = getattr(subitem, 'toggleTitle', None)
                        toggleMnemonic = extractMnemonic(subitem, toggleTitle)
                        
                        if toggleTitle:
                            if toggleMnemonic is None:
                                self._appendFailure("Missing mnemonic for %s", (subitem, toggleTitle))
                            elif toggleMnemonic != mnemonic:
                                updateDict(toggleMnemonic, (subitem, toggleTitle))

            for mnemonic, items in mnemonicToItems.iteritems():
                if len(items) > 1:
                    fmt = "Collision for mnemonic '%s':\n---Mnemonics used in this menu: <%s>---\n" + len(items) * "\n   %s"
                    # Since we know all the keys in play for this
                    # menu, let's include them in the error message to make
                    # fixing this easier.
                    used = ''.join(sorted(mnemonicToItems.keys()))
                    self._appendFailure(fmt, mnemonic, used, *items)
        self.checkFailures()

    def testShortcuts(self):
        # This tests "global shortcuts", i.e. Accelerators, a.k.a. 
        # Control-Key combinations (Win/Linux) a.k.a. Command-Key equivalents
        # (Mac).
        #
        # For uniqueness, we want to make sure that a given shortcut is
        # used at most once in a given menu hierarchy: It's somewhat odd,
        # but in theory possible, to have a shortcut be used in a context
        # menu as well as a regular menu.
        #
        # For this to work, we use as a key in shortcutToItems the following
        # tuple for each accelerator we find:
        #
        # UUID of "root menu" (calculated below)
        # sorted modifiers
        # the key
        VALID_MODIFIERS = ('Shift', 'Ctrl', 'Alt')
        VALID_MULTIKEYS = ('Back', 'Del', 'Left', 'Right', 'Up', 'Down') + tuple(
                              'F%d' % i for i in range(1, 13, 1))
        shortcutsToItems = {}

        for menu in self.Menu.iterItems(self.view):
            # Calculate rootMenu, the topmost menu-like block this menu
            # can be traced back to.
            rootMenu = menu
            while isinstance(rootMenu.parentBlock,
                             (self.Menu, self.MenuItem)):
                rootMenu = rootMenu.parentBlock

            # Now iterate over the submenu items, trying to find accelerators.
            for subitem in menu.childBlocks:
                accel = getattr(subitem, 'accel', None)
                if accel:
                    splitAccel = accel.split("+")
                    bogusAccels = [a for a in splitAccel[:-1] if not a in VALID_MODIFIERS]
                    if bogusAccels:
                        self._appendFailure("Incorrect modifiers %s in %s: Must be one of %s", ("+".join(bogusAccels)), accel, ",".join(VALID_MODIFIERS))
                    key = splitAccel[-1]
                    # All keys I could find in wx are titlecase (i.e. capital
                    # first letter), so let's check that
                    if key != key.title():
                        self._appendFailure("Incorrect accelerator %s in %s:Key is not title-case", accel, subitem)
                    elif len(key) > 1 and key not in VALID_MULTIKEYS:
                        self._appendFailure("Incorrect accelerator %s in %s: Key %s not recognized", accel, subitem, key)
                    else:
                        mods = splitAccel[:-1]
                        
                        t = tuple(itertools.chain(
                                    [rootMenu.itsUUID],
                                    sorted(mods),
                                    key))
                        items = shortcutsToItems.setdefault(t, [])
                        items.append(subitem)

        for t, items in shortcutsToItems.iteritems():
            if len(items) > 1:
                    fmt = "Collision for shortcut '%s':\n" + len(items) * "\n   %s"
                    self._appendFailure(fmt, items[0].accel, *items)
        self.checkFailures()

if __name__ == "__main__":
    options = Utility.initOptions()
    argv = list(itertools.chain((sys.argv[0],), options.args))
    unittest.main(argv=argv)

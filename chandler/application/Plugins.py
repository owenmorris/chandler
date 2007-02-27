#   Copyright (c) 2007-2007 Open Source Applications Foundation
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

import os, pkg_resources, wx

from application import schema, Utility, Globals, Parcel
from osaf.framework.blocks import Menu, MenuItem, BlockEvent
from osaf.framework.blocks.Block import Block
from repository.schema.Kind import Kind
from i18n import ChandlerMessageFactory as _


class PluginMenu(Menu):

    def __init__(self, *args, **kwds):

        super(PluginMenu, self).__init__(*args, **kwds)

        BlockEvent(itsName='_plugins', itsParent=self, blockName='_plugins',
                   dispatchEnum='SendToBlockByReference',
                   destinationBlockReference=self)

    def onItemLoad(self, view):

        self.prefs = Utility.loadPrefs(Globals.options).get('plugins', {})

    def ensureDynamicChildren(self):

        prefs = Utility.loadPrefs(Globals.options).get('plugins', {})
        self.prefs = prefs

        for item in self.dynamicChildren:
            if item.itsName not in prefs:
                item.delete()

        for title in sorted(prefs.iterkeys()):
            if not self.hasChild(title):
                MenuItem(itsName=title, itsParent=self, dynamicParent=self,
                         event=self.getItemChild('_plugins'), parentBlock=self,
                         title=title, blockName=title,
                         menuItemKind='Check')

    def on_pluginsEvent(self, event):

        name = event.arguments['sender'].itsName

        if self.prefs.get(name, 'active') == 'active':
            dlg = wx.MessageDialog(wx.GetApp().mainFrame,
                                   _(u"All items from plugin %(pluginName)s will be deleted.") %{'pluginName': name}, 
                                   _(u"Confirm Deactivation"),
                                   (wx.YES_NO | wx.YES_DEFAULT |
                                    wx.ICON_EXCLAMATION))
            cmd = dlg.ShowModal()
            dlg.Destroy()
            if cmd == wx.ID_YES:
                self.deactivatePlugin(name)
        else:
            self.activatePlugin(name)

    def on_pluginsEventUpdateUI(self, event):

        args = event.arguments
        check = self.prefs.get(args['sender'].itsName, 'active') == 'active'
        args['Check'] = check

    def activatePlugin(self, project_name):

        view = self.itsView
        prefs = Utility.loadPrefs(Globals.options)
        plugin_env = pkg_resources.Environment(Globals.options.pluginPath)

        entrypoints = []
        for egg in plugin_env[project_name]:
            pkg_resources.working_set.add(egg)

            for ep in egg.get_entry_map('chandler.parcels').values():
                try:
                    ep.require(plugin_env)
                except pkg_resources.ResolutionError:
                    return # log error
                else:
                    entrypoints.append((egg.key, ep))
            break

        for name, ep in entrypoints:
            Parcel.load_parcel_from_entrypoint(view, ep)
            self.prefs[name] = 'active'

        if 'plugins' not in prefs:
            prefs['plugins'] = self.prefs
        else:
            prefs['plugins'].update(self.prefs)
            self.prefs = prefs['plugins']

        view.commit()
        prefs.write()

        self.restartApp(_(u"Plugin was activated: %s") %(egg.egg_name()))

    def deactivatePlugin(self, project_name):

        view = self.itsView
        prefs = Utility.loadPrefs(Globals.options)
        plugin_env = pkg_resources.Environment(Globals.options.pluginPath)

        entrypoints = []
        for egg in plugin_env[project_name]:
            for ep in egg.get_entry_map('chandler.parcels').values():
                entrypoints.append((egg.key, ep))
            break

        def deleteItems(item):
            for child in item.iterChildren():
                deleteItems(child)
            if isinstance(item, Kind):
                for instance in item.iterItems():
                    instance.delete(True)

        for name, ep in entrypoints:
            parcel = Parcel.find_parcel_from_entrypoint(view, ep)
            if parcel is not None:
                deleteItems(parcel)
                parcel.delete(True)
            self.prefs[name] = 'inactive'

        if 'plugins' not in prefs:
            prefs['plugins'] = self.prefs
        else:
            prefs['plugins'].update(self.prefs)
            self.prefs = prefs['plugins']

        view.commit()
        prefs.write()

        self.restartApp(_(u"Plugin was deactivated: %s.") %(egg.egg_name()))

    def restartApp(self, msg):

        app = wx.GetApp()
        dlg = wx.MessageDialog(app.mainFrame,
                               _(u"%s\nChandler will now restart") %(msg),
                               _(u"Confirm Restart"),
                               (wx.YES_NO | wx.YES_DEFAULT |
                                wx.ICON_EXCLAMATION))
        cmd = dlg.ShowModal()
        dlg.Destroy()
        if cmd == wx.ID_YES:
            app.PostAsyncEvent(app.restart)

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

import os, pkg_resources, wx, webbrowser, logging

from application import schema, Utility, Globals, Parcel
from osaf.framework.blocks import Menu, MenuItem, BlockEvent
from osaf.framework.blocks.Block import Block
from repository.schema.Kind import Kind
from i18n import ChandlerMessageFactory as _

BROWSE_URL = "http://cheeseshop.python.org/pypi?:action=browse&c=519"
logger = logging.getLogger(__name__)


class PluginMenu(Menu):

    def __setup__(self):
        BlockEvent(itsName='_plugins', itsParent=self,
                   blockName='_plugins',
                   dispatchEnum='SendToBlockByReference',
                   destinationBlockReference=self)

    def onItemLoad(self, view):

        self.prefs = Utility.loadPrefs(Globals.options).get('plugins', {})

    def ensureDynamicChildren(self):

        prefs = Utility.loadPrefs(Globals.options).get('plugins', {})
        self.prefs = prefs

        for item in self.dynamicChildren:
            if item.itsName is not None and item.itsName not in prefs:
                item.delete()

        for block in self.dynamicChildren:
            if block.blockName == '_browse_menu':
                break
        else:
            for child in self.iterChildren():
                if getattr(child, 'blockName', None) == '_browse_menu':
                    self.dynamicChildren.append(child)
                    self.dynamicChildren.append(self.getNextChild(child))
                    break
            else:
                MenuItem(itsName=None, itsParent=self,
                         blockName='_browse_menu',
                         event=BlockEvent(itsName='_browse', itsParent=self,
                                          blockName='_browse',
                                          dispatchEnum='SendToBlockByReference',
                                          destinationBlockReference=self),
                         parentBlock=self, dynamicParent=self,
                         title="Download Plugins")
                MenuItem(itsName=None, itsParent=self,
                         blockName='_separator',
                         parentBlock=self, dynamicParent=self,
                         menuItemKind='Separator')

        for title in sorted(prefs.iterkeys()):
            if not self.hasChild(title):
                MenuItem(itsName=title, itsParent=self, dynamicParent=self,
                         event=self.getItemChild('_plugins'), parentBlock=self,
                         title=title, blockName=title,
                         menuItemKind='Check')

    def on_browseEvent(self, event):

        webbrowser.open(BROWSE_URL)

    def on_pluginsEvent(self, event):

        msg = ''
        statusBar = Block.findBlockByName('StatusBar')
        statusBar.setStatusMessage(msg)

        name = event.arguments['sender'].itsName
        plugin_env = pkg_resources.Environment(Globals.options.pluginPath)

        if self.prefs.get(name, 'active') == 'active':

            for egg in plugin_env[name]:
                break
            else:
                return

            for ep in pkg_resources.iter_entry_points('chandler.parcels'):
                if plugin_env[ep.dist.key]:  # only handle plugin entrypoints
                    requires = ep.dist.requires(ep.extras)
                    if egg in pkg_resources.working_set.resolve(requires):
                        if self.prefs.get(ep.dist.key, 'inactive') == 'active':
                            dlg = wx.MessageDialog(None,
                                                   _(u"%(pluginName)s is required by %(eggName)s.\n\n%(eggName)s must be deactivated first.") %{'eggName': ep.dist.egg_name(), 'pluginName': egg.egg_name()},
                                                   _(u"Error"),
                                                   wx.OK | wx.ICON_ERROR)
                            cmd = dlg.ShowModal()
                            dlg.Destroy()
                            return

            dlg = wx.MessageDialog(None,
                                   _(u"All items created by plugin %(pluginName)s will be deleted.") %{'pluginName': egg.egg_name()}, 
                                   _(u"Confirm Deactivation"),
                                   (wx.YES_NO | wx.YES_DEFAULT |
                                    wx.ICON_EXCLAMATION))
            cmd = dlg.ShowModal()
            dlg.Destroy()
            if cmd == wx.ID_YES:
                egg = self.deactivatePlugin(name, plugin_env)
                if egg is not None:
                    msg = _(u"%(pluginName)s was deactivated.") %{'pluginName': egg.egg_name()}
                else:
                    return
            else:
                return

        else:
            egg, dependencies = self.activatePlugin(name, plugin_env)
            if egg is not None:
                if not dependencies:
                    msg = _(u"%(pluginName)s was activated.") %{'pluginName': egg.egg_name()}
                else:
                    msg = _(u"%(pluginName)s and %(pluginNames)s were activated.") %{'pluginName': egg.egg_name(), 'pluginNames': ', '.join([dist.egg_name() for dist in dependencies])}
            else:
                return

        # Update the menus
        wx.GetApp().GetActiveView().rebuildDynamicBlocks()
        statusBar.setStatusMessage(msg)

    def on_pluginsEventUpdateUI(self, event):

        args = event.arguments
        check = self.prefs.get(args['sender'].itsName, 'active') == 'active'
        args['Check'] = check

    def activatePlugin(self, project_name, plugin_env):

        view = self.itsView
        prefs = Utility.loadPrefs(Globals.options)

        for egg in plugin_env[project_name]:
            pkg_resources.working_set.add(egg)

            for ep in egg.get_entry_map('chandler.parcels').values():
                try:
                    ep.require(plugin_env)
                    requires = egg.requires(ep.extras)
                except pkg_resources.ResolutionError:
                    logger.exception("Activating %s failed", egg.egg_name())
                    return None, None
            break
        else:
            return None, None

        dependencies = pkg_resources.working_set.resolve(requires)

        for ep in pkg_resources.iter_entry_points('chandler.parcels'):
            name = ep.dist.key
            if plugin_env[name]:  # only handle plugin entrypoints
                if ep.dist == egg or ep.dist in dependencies: 
                    if self.prefs.get(name, 'inactive') == 'inactive':
                        Parcel.load_parcel_from_entrypoint(view, ep)
                        self.prefs[name] = 'active'
                    else:
                        dependencies.remove(ep.dist)

        if 'plugins' not in prefs:
            prefs['plugins'] = self.prefs
        else:
            prefs['plugins'].update(self.prefs)
            self.prefs = prefs['plugins']

        view.commit()
        prefs.write()

        return egg, dependencies

    def deactivatePlugin(self, project_name, plugin_env):

        view = self.itsView
        prefs = Utility.loadPrefs(Globals.options)

        for egg in plugin_env[project_name]:
            break
        else:
            return None

        def deleteItems(item):
            for child in item.iterChildren():
                deleteItems(child)
            if isinstance(item, Kind):
                for instance in item.iterItems():
                    instance.delete(True)

        for ep in egg.get_entry_map('chandler.parcels').values():
            parcel = Parcel.find_parcel_from_entrypoint(view, ep)
            if parcel is not None:
                deleteItems(parcel)
                parcel.delete(True)
            self.prefs[ep.dist.key] = 'inactive'

        if 'plugins' not in prefs:
            prefs['plugins'] = self.prefs
        else:
            prefs['plugins'].update(self.prefs)
            self.prefs = prefs['plugins']

        view.commit()
        prefs.write()

        return egg

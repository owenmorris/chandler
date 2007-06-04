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

from application import Utility, Globals, Parcel, schema
from osaf.framework.blocks import Menu
from osaf.framework.blocks.MenusAndToolbars import wxMenu, wxMenuItem
from osaf.framework.blocks.Block import Block
from repository.schema.Kind import Kind
from i18n import ChandlerMessageFactory as _

BROWSE_URL = "http://cheeseshop.python.org/pypi?:action=browse&c=519"
logger = logging.getLogger(__name__)


class wxPluginMenu(wxMenu):

    def ItemsAreSame(self, old, new):

        if new is None or isinstance(new, wx.MenuItem):
            return super(wxPluginMenu, self).ItemsAreSame(old, new)

        if new == '__separator__':
            return old is not None and old.IsSeparator()
        else:
            return old is not None and old.GetText() == new
    
    def GetNewItems(self):

        newItems = super(wxPluginMenu, self).GetNewItems()

        titles = sorted(self.pluginPrefs.iterkeys())
        if titles:
            newItems.extend(titles)

        return newItems

    def InsertItem(self, position, item):

        if not isinstance(item, wx.MenuItem):
            if item == '__separator__':
                item = wx.MenuItem(self, id=wx.ID_SEPARATOR,
                                   kind=wx.ID_SEPARATOR)
            else:
                block = Block.findBlockByName("PluginsMenu")
                id = block.getWidgetID()
                item = wx.MenuItem(self, id=id, text=item, kind=wx.ITEM_CHECK)

        super(wxPluginMenu, self).InsertItem(position, item)


class PluginMenu(Menu):

    def instantiateWidget(self):

        menu = wxPluginMenu()
        menu.blockItem = self
        menu.pluginPrefs = Utility.loadPrefs(Globals.options).get('plugins', {})

        # if we don't give the MenuItem a label, i.e. test = " " widgets
        # will use the assume the id is for a stock menuItem and will fail
        return wxMenuItem(None, id=self.getWidgetID(), text=" ", subMenu=menu)

    def onBrowsePluginsEvent(self, event):
        webbrowser.open(BROWSE_URL)

    def onInstallPluginsEvent(self, event):

        patterns = "%s|*.tar.gz|%s|*.tar|%s (*.*)|*.*" %(_(u"tar/gz archives"),
                                                         _(u"tar archives"),
                                                         _(u"All files"))
        dlg = wx.FileDialog(None, _(u"Install Plugin"), "", "", patterns,
                            wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            archive = dlg.GetPath()
        else:
            archive = None
        dlg.Destroy()

        if archive is not None:
            options = Globals.options
            pluginsDir = options.pluginPath[0]
            if not os.path.exists(pluginsDir):
                os.makedirs(pluginsDir)

            try:
                from setuptools.command.easy_install import main
                from distutils.log import _global_log

                # patch distutils' logger with logging's
                # distutils logging levels happen to be one tenth of logging's
                def log(level, msg, args):
                    logger.log(level * 10, msg, *args)

                _log = _global_log._log
                _global_log._log = log

                main(['--multi-version', '--install-dir', pluginsDir, archive])
            finally:
                _global_log._log = _log

            env, eggs = Utility.initPluginEnv(options, options.pluginPath)
            prefs = Utility.initPlugins(options, self.itsView, env, eggs)

            # Update the menus
            self.widget.GetSubMenu().pluginPrefs = prefs.get('plugins', {})
            self.synchronizeWidget()
            self.refreshMenus(self.itsView);

    def onPluginEvent(self, event):

        msg = ''
        statusBar = Block.findBlockByName('StatusBar')
        statusBar.setStatusMessage(msg)

        subMenu = self.widget.GetSubMenu()
        menuItem = subMenu.FindItemById(event.arguments["wxEvent"].GetId())
        name = menuItem.GetText()

        plugin_env = pkg_resources.Environment(Globals.options.pluginPath)
        pluginPrefs = subMenu.pluginPrefs

        if pluginPrefs.get(name, 'active') == 'active':

            for egg in plugin_env[name]:
                break
            else:
                return

            for ep in pkg_resources.iter_entry_points('chandler.parcels'):
                if plugin_env[ep.dist.key]:  # only handle plugin entrypoints
                    requires = ep.dist.requires(ep.extras)
                    if egg in pkg_resources.working_set.resolve(requires):
                        if pluginPrefs.get(ep.dist.key, 'inactive') == 'active':
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
        self.synchronizeWidget()
        self.refreshMenus(self.itsView);
        statusBar.setStatusMessage(msg)

    def onPluginEventUpdateUI(self, event):

        arguments = event.arguments
        widget = self.widget
        subMenu = widget.GetSubMenu()
        menuItem = subMenu.FindItemById(arguments["wxEvent"].GetId())

        if isinstance(menuItem, wx.MenuItem):
            value = subMenu.pluginPrefs.get(menuItem.GetText(), 'active')
            arguments['Check'] = value == 'active'
            
            # Delete default text since.
            del arguments['Text']

    def activatePlugin(self, project_name, plugin_env):

        view = self.itsView
        prefs = Utility.loadPrefs(Globals.options)
        pluginPrefs = self.widget.GetSubMenu().pluginPrefs

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
                    if pluginPrefs.get(name, 'inactive') == 'inactive':
                        Parcel.load_parcel_from_entrypoint(view, ep)
                        pluginPrefs[name] = 'active'
                    else:
                        dependencies.remove(ep.dist)

        if 'plugins' not in prefs:
            prefs['plugins'] = pluginPrefs
        else:
            prefs['plugins'].update(pluginPrefs)
            self.widget.GetSubMenu().pluginPrefs = prefs['plugins']

        prefs.write()

        return egg, dependencies

    def deactivatePlugin(self, project_name, plugin_env):

        view = self.itsView
        prefs = Utility.loadPrefs(Globals.options)
        pluginPrefs = self.widget.GetSubMenu().pluginPrefs

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
            pluginPrefs[ep.dist.key] = 'inactive'

        if 'plugins' not in prefs:
            prefs['plugins'] = pluginPrefs
        else:
            prefs['plugins'].update(pluginPrefs)
            self.widget.GetSubMenu().pluginPrefs = prefs['plugins']

        prefs.write()

        return egg

    def refreshMenus(self, view):

        menubar = schema.ns('osaf.views.main', view).MenuBar
        for menu in menubar.childBlocks:
            if menu.isDirty():
                menu.synchronizeWidget()


class wxDemoMenu(wxMenu):

    def ItemsAreSame(self, old, new):

        if new is None or isinstance(new, wx.MenuItem):
            return super(wxDemoMenu, self).ItemsAreSame(old, new)

        if new == '__separator__':
            return old is not None and old.IsSeparator()
        else:
            return old is not None and old.GetText() == new
    
    def GetNewItems(self):

        newItems = super(wxDemoMenu, self).GetNewItems()
        if len(newItems) > 2 and not newItems[2].IsSeparator():
            newItems.insert(2, '__separator__')

        return newItems

    def InsertItem(self, position, item):

        if not isinstance(item, wx.MenuItem):
            if item == '__separator__':
                item = wx.MenuItem(self, id=wx.ID_SEPARATOR,
                                   kind=wx.ID_SEPARATOR)

        super(wxDemoMenu, self).InsertItem(position, item)


class DemoMenu(Menu):

    def instantiateWidget(self):

        menu = wxDemoMenu()
        menu.blockItem = self

        # if we don't give the MenuItem a label, i.e. test = " " widgets
        # will assume the id is for a stock menuItem and will fail
        return wxMenuItem(None, id=self.getWidgetID(), text=" ", subMenu=menu)

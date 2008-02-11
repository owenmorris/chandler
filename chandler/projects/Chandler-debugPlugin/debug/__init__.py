#   Copyright (c) 2007 Open Source Applications Foundation
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

from application import schema
from osaf.framework.blocks import BlockEvent, ChoiceEvent, MenuItem, Menu
from osaf.framework.blocks.Block import Block

from debug.TestMenu import makeTestMenu
from debug.DebugMenu import makeDebugMenu
from debug.MeMenu import makeMeMenu
from debug.SharingMenu import makeSharingMenu


def installParcel(parcel, version=None):

    toolsMenu = schema.ns('osaf.views.main', parcel).ToolsMenu
    sharingMenu = schema.ns('osaf.views.main', parcel).ShareTestMenu

    MenuItem.update(parcel, None,
                    blockName='_debug_separator_0',
                    menuItemKind='Separator',
                    parentBlock=toolsMenu)

    makeTestMenu(parcel, toolsMenu)
    makeDebugMenu(parcel, toolsMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_separator_1',
                    menuItemKind='Separator',
                    parentBlock=sharingMenu)

    makeMeMenu(parcel, sharingMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_separator_2',
                    menuItemKind='Separator',
                    parentBlock=sharingMenu)

    makeSharingMenu(parcel, sharingMenu)

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
from i18n import MessageFactory

from osaf.framework.blocks.Block import Block
from osaf.framework.blocks import BlockEvent, ChoiceEvent, MenuItem, Menu
from repository.item.Item import Item

_m_ = MessageFactory("Chandler-debugPlugin")


def makeCPIAMenu(parcel, toolsMenu):

    chooseChandlerEvent = \
        ChoiceEvent.update(parcel, 'ChooseChandlerMainView',
                           blockName='_debug_ChooseChandlerMainView',
                           methodName='onChoiceEvent',
                           choice = 'MainView',
                           dispatchToBlockName='MainViewRoot')

    chooseCPIATestEvent = \
        ChoiceEvent.update(parcel, 'ChooseCPIATestMainView',
                           blockName='_debug_ChooseCPIATestMainView',
                           methodName='onChoiceEvent',
                           choice='CPIATestMainView',
                           dispatchToBlockName='MainViewRoot')

    chooseCPIATest2Event = \
        ChoiceEvent.update(parcel, 'ChooseCPIATest2MainView',
                           blockName='_debug_ChooseCPIATest2MainView',
                           methodName='onChoiceEvent',
                           choice='CPIATest2MainView',
                           dispatchToBlockName='MainViewRoot')

    cpiaMenu = Menu.update(parcel, None,
                           blockName='_debug_cpiaMenu',
                           title=_m_(u'CPI&A'),
                           parentBlock=toolsMenu)
    
    MenuItem.update(parcel, None,
                    blockName='_debug_ChandlerSkinMenuItem',
                    title=_m_(u'&Chandler Skin'),
                    menuItemKind='Check',
                    helpString=_m_(u'Switch to Chandler'),
                    event = chooseChandlerEvent,
                    parentBlock=cpiaMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_CPIATestMenuItem',
                    title=_m_(u'C&PIA Test Skin'),
                    menuItemKind='Check',
                    helpString=_m_(u'Switch to CPIA test'),
                    event = chooseCPIATestEvent,
                    parentBlock=cpiaMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_CPIATest2MenuItem',
                    title=_m_(u'CPIA Test &2 Skin'),
                    menuItemKind='Check',
                    helpString=_m_(u'Switch to CPIA test 2'),
                    event = chooseCPIATest2Event,
                    parentBlock=cpiaMenu)

    # Create the main views for cpiatest and cpiatest2 in separate containers
    # so that item names don't clash.
    # Add a copy of the cpiaMenu above to the tools menu in each mainView
    # thus created. The first child of the main view is the MenuBar.

    views = schema.ns('osaf.views.main', parcel).MainViewRoot.views

    from cpiatest.mainblocks import makeCPIATestMainView
    cpiatest = Item('cpiatest', parcel)
    views['CPIATestMainView'] = mainView = makeCPIATestMainView(cpiatest)
    for childBlock in mainView.childBlocks.first().childBlocks:
        if childBlock.itsName == 'ToolsMenu':
            childBlock.childBlocks.append(cpiaMenu.copy(parent=cpiatest,
                                                        cloudAlias="copying"))
            break

    from cpiatest2.mainblocks import makeCPIATest2MainView
    cpiatest2 = Item('cpiatest2', parcel)
    views['CPIATest2MainView'] = mainView = makeCPIATest2MainView(cpiatest2)
    for childBlock in mainView.childBlocks.first().childBlocks:
        if childBlock.itsName == 'ToolsMenu':
            childBlock.childBlocks.append(cpiaMenu.copy(parent=cpiatest2,
                                                        cloudAlias="copying"))
            break

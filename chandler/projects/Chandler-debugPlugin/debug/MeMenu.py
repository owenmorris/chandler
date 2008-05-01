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


from application import schema, dialogs
from i18n import MessageFactory

from osaf.pim import mail
from osaf.framework.blocks.Block import Block
from osaf.framework.blocks import BlockEvent, MenuItem, Menu

_ = MessageFactory("Chandler-debugPlugin")


class MeMenuHandler(Block):

    def displayAddressDebugWindow(self, type=1):
        # Types:
        # =========
        # 1: meEmailAddressCollection
        # 2: currentMeEmailAddresses
        # 3: currenMeEmailAddress

        pim = schema.ns('osaf.pim', self.itsView)

        if type == 1:
            collection = pim.meEmailAddressCollection
        elif type == 2:
            collection = pim.currentMeEmailAddresses
        else:
            collection = [pim.currentMeEmailAddress.item]

        list = [eAddr.format() for eAddr in collection if eAddr]

        win = dialogs.Util.DebugWindow(u"Email Address Debugger",
                                       u'\n'.join(list), tsize=[400, 300])
        win.CenterOnScreen()
        win.ShowModal()
        win.Destroy()

    def on_debug_EditMyNameEvent(self, event):
        dialogs.Util.promptForItemValues(_(u"Enter your name"),
            schema.ns('osaf.pim', self.itsView).currentContact.item.contactName,
            ( {'attr':'firstName', 'label':'First name' },
              {'attr':'lastName', 'label':'Last name' } )
        )

    def on_debug_ShowMeAddressCollectionDebugWindowEvent(self, event):
        self.displayAddressDebugWindow(1)

    def on_debug_ShowCurrentMeAddressesDebugWindowEvent(self, event):
        self.displayAddressDebugWindow(2)

    def on_debug_ShowCurrentMeAddressDebugWindowEvent(self, event):
        self.displayAddressDebugWindow(3)

    def on_debug_RecalculateMeAddressesEvent(self, event):
        mail._recalculateMeEmailAddresses(self.itsView)


def makeMeMenu(parcel, sharingMenu):

    handler = MeMenuHandler.update(parcel, None,
                                   blockName='_debug_MeMenuHandler')

    editMyNameEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_EditMyName',
                          dispatchEnum='SendToBlockByReference',
                          commitAfterDispatch=True,
                          destinationBlockReference=handler)
    showMeAddressCollectionDebugWindowEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_ShowMeAddressCollectionDebugWindow',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)
    showCurrentMeAddressesDebugWindowEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_ShowCurrentMeAddressesDebugWindow',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)
    showCurrentMeAddressDebugWindowEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_ShowCurrentMeAddressDebugWindow',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)
    recalculateMeAddressesEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_RecalculateMeAddresses',
                          dispatchEnum='SendToBlockByReference',
                          commitAfterDispatch=True,
                          destinationBlockReference=handler)

    MenuItem.update(parcel, None,
                    blockName='_debug_EditMyName',
                    title=_(u'Edit "Me" &name...'),
                    helpString=_(u'Edit your name'),
                    event=editMyNameEvent,
                    parentBlock=sharingMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_ShowMeAddressCollectionDebugWindow',
                    title=_(u'Show "Me" Address &Collection...'),
                    helpString=_(u'Displays all active and old me addresses used to determine the fromMe and toMe attributes on Content Item'),
                    event=showMeAddressCollectionDebugWindowEvent,
                    parentBlock=sharingMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_ShowCurrentMeAddressesDebugWindow',
                    title=_(u'Show Current &Me Addresses...'),
                    helpString=_(u'Displays all active me addresses'),
                    event=showCurrentMeAddressesDebugWindowEvent,
                    parentBlock=sharingMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_ShowCurrentMeAddressDebugWindow',
                    title=_(u'&Show Current Me Address...'),
                    helpString=_(u'Displays the current me address'),
                    event=showCurrentMeAddressDebugWindowEvent,
                    parentBlock=sharingMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_recalculateEmailAddressItem',
                    title=_(u'&Recalculate Me Addresses'),
                    helpString=_(u'Loops through the Incoming and Outgoing Accounts and rebuilds the me addresses current references'),
                    event=recalculateMeAddressesEvent,
                    parentBlock=sharingMenu)

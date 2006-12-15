#   Copyright (c) 2006 Open Source Applications Foundation
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


from datetime import timedelta
from application import schema
from i18n import MessageFactory
from osaf.startup import PeriodicTask
from osaf.framework.blocks import BlockEvent, MenuItem

from dialogs import p2pHandler, setStatusMessage
from account import findDefaultAccounts, AllGroup


_m_ = MessageFactory("Chandler-p2pPlugin")


class LoginTask(object):
    
    def __init__(self, item):

        self.view = item.itsView
        
    def run(self):

        for account in findDefaultAccounts(self.view):
            account.login(setStatusMessage, True)

        schema.ns('p2p', self.view).loginTask.stop()
        return True


def installParcel(parcel, version=None):

    main = schema.ns('osaf.views.main', parcel)

    handler = p2pHandler.update(parcel, 'p2pHandler',
                                blockName='_p2p_p2pHandler')

    # Add an event for p2p subscribing to collections
    subscribeEvent = BlockEvent.update(parcel, None,
                                       blockName='_p2p_Subscribe',
                                       dispatchEnum='SendToBlockByReference',
                                       destinationBlockReference=handler)
    # Add an event for p2p login
    loginEvent = BlockEvent.update(parcel, None,
                                   blockName='_p2p_Login',
                                   dispatchEnum='SendToBlockByReference',
                                   destinationBlockReference=handler)
    # Add an event for managing p2p access to collections
    accessEvent = BlockEvent.update(parcel, None,
                                    blockName='_p2p_Access',
                                    dispatchEnum='SendToBlockByReference',
                                    destinationBlockReference=handler)
    # Add an event send a collection via p2p email
    sendMailEvent = BlockEvent.update(parcel, None,
                                      blockName='_p2p_SendMail',
                                      dispatchEnum='SendToBlockByReference',
                                      destinationBlockReference=handler)
    # Add an event check for p2p email
    checkMailEvent = BlockEvent.update(parcel, None,
                                       blockName='_p2p_CheckMail',
                                       dispatchEnum='SendToBlockByReference',
                                       destinationBlockReference=handler)


    # Add a separator to the "Experimental" menu ...
    MenuItem.update(parcel, 'menuSeparator',
                    blockName='_p2p_menuSeparator',
                    menuItemKind='Separator',
                    parentBlock=main.ExperimentalMenu)

    # Add a menu item to the "Experimental" menu to login to a peer network
    MenuItem.update(parcel, "LoginMenuItem",
                    blockName="_p2p_LoginMenuItem",
                    title=_m_(u"Login to a peer network"),
                    event=loginEvent,
                    eventsForNamedLookup=[loginEvent],
                    parentBlock=main.ExperimentalMenu)

    # ... and, below it, a menu item to p2p subscribe to a collection
    MenuItem.update(parcel, "SubscribeMenuItem",
                    blockName="_p2p_SubscribeMenuItem",
                    title=_m_(u"Subscribe to a peer collection"),
                    event=subscribeEvent,
                    eventsForNamedLookup=[subscribeEvent],
                    parentBlock=main.ExperimentalMenu)

    # ... and, below it, a menu item to manage p2p permissions to a collection
    MenuItem.update(parcel, "AccessMenuItem",
                    blockName="_p2p_AccessMenuItem",
                    title=_m_(u"Grant peer access to ..."),
                    event=accessEvent,
                    eventsForNamedLookup=[accessEvent],
                    parentBlock=main.ExperimentalMenu)

    # ... and, below it, a menu item to send a collection via email
    MenuItem.update(parcel, "SendMailMenuItem",
                    blockName="_p2p_SendMailMenuItem",
                    title=_m_(u"Send ... via p2p email"),
                    event=sendMailEvent,
                    eventsForNamedLookup=[sendMailEvent],
                    parentBlock=main.ExperimentalMenu)

    # ... and, below it, a menu item to check for p2p email
    MenuItem.update(parcel, "CheckMailMenuItem",
                    blockName="_p2p_CheckMailMenuItem",
                    title=_m_(u"Check p2p email"),
                    event=checkMailEvent,
                    eventsForNamedLookup=[checkMailEvent],
                    parentBlock=main.ExperimentalMenu)

    PeriodicTask.update(parcel, "loginTask",
                        invoke="_p2p_LoginTask",
                        interval=timedelta(days=1),
                        run_at_startup=True)

    AllGroup.update(parcel, "all", name="All")

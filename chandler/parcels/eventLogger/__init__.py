#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


__parcel__ = "eventLogger"

from application import schema
from osaf.framework.blocks import DispatchHook, BlockEvent
from osaf.framework.blocks.MenusAndToolbars import MenuItem
from i18n import OSAFMessageFactory as _

class EventLoggingDispatchHook (DispatchHook):
    logging = schema.One(schema.Boolean, initialValue=False)

    def dispatchEvent (self, event, depth):
        print event, depth

    def onToggleLoggingEvent (self, event):
        self.logging = not self.logging

        hooksListItem = schema.ns ('osaf.framework.blocks', self.itsView).BlockDispatchHookList
        dispatchHook = schema.ns (__name__, self.itsView).EventLoggingHook
        if self.logging:
            hooksListItem.hooks.insertItem (dispatchHook, None)
        else:
            hooksListItem.hooks.remove (dispatchHook)


    def onToggleLoggingEventUpdateUI (self, event):
        event.arguments['Check'] = self.logging


def installParcel(parcel, old_version=None):
    mainView = schema.ns('osaf.views.main', parcel.itsView)

    dispatchHook = EventLoggingDispatchHook.update(
        parcel, 'EventLoggingHook',
        blockName = 'EventLoggingHook')

    # Event to toggle logging
    ToggleLogging = BlockEvent.update(
        parcel, 'ToggleLogging',
        blockName = 'ToggleLogging',
        dispatchEnum = 'SendToBlockByReference',
        destinationBlockReference = dispatchHook)

    # Add menu item to Chandler
    MenuItem.update(
        parcel, 'StartLogging',
        blockName = 'StartLoggingMenuItem',
        menuItemKind = 'Check',
        title = _(u'Start Logging'),
        helpString = _(u'Turn on logging and send result to OSAF'),
        event = ToggleLogging,
        eventsForNamedLookup = [ToggleLogging],
        # Recent changes have broken the menu location code
        #location = "TestMenu",
        #itemLocation = "RepositoryTestMenu",
        #parentBlock = mainView.MainView
         parentBlock = mainView.TestMenu)
 


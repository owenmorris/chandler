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

import os, sys

from application import schema
from i18n import MessageFactory

from osaf.framework.blocks import BlockEvent, MenuItem
from osaf.framework.blocks.Block import Block

from sidebar import sidebar

_ = MessageFactory("Chandler-fusePlugin")
MOUNT_NAME='Sidebar'


class fuseHandler(Block):

    def __setup__(self):
        self.onItemLoad(None)

    def onItemLoad(self, view):
        self.setPinned(True)
        self.sidebar = None

    def on_fuse_MountEventUpdateUI(self, event):

        if sys.platform == 'darwin':
            if self.sidebar is not None and self.sidebar.isMounted():
                menuTitle = u'Remove Sidebar from Finder'
            else:
                menuTitle = u'Show Sidebar in Finder'
        else:
            mountpoint = os.path.expanduser('~/%s' %(MOUNT_NAME))
            if self.sidebar is not None and self.sidebar.isMounted():
                menuTitle = u'Remove Sidebar from %s' %(mountpoint)
            else:
                menuTitle = u'Show Sidebar in %s' %(mountpoint)

        event.arguments['Text'] = menuTitle

    def on_fuse_MountEvent(self, event):

        if self.sidebar is None or not self.sidebar.isMounted():
            self.sidebar = sidebar(self.itsView.repository)
            if sys.platform == 'darwin':
                mountpoint = '/Volumes/%s' %(MOUNT_NAME)
                self.sidebar.mount(mountpoint, volname=MOUNT_NAME)
            else:
                mountpoint = os.path.expanduser('~/%s' %(MOUNT_NAME))
                self.sidebar.mount(mountpoint)
        else:
            self.sidebar.umount()


def installParcel(parcel, version=None):

    main = schema.ns('osaf.views.main', parcel)
    handler = fuseHandler.update(parcel, '_fuse_fuseHandler',
                                 blockName='_fuse_fuseHandler')

    # Add an event for mount/umount
    mountEvent = BlockEvent.update(parcel, None,
                                   blockName='_fuse_Mount',
                                   dispatchEnum='SendToBlockByReference',
                                   destinationBlockReference=handler)

    # Add a separator to the "Experimental" menu ...
    MenuItem.update(parcel, 'menuSeparator',
                    blockName='_fuse_menuSeparator',
                    menuItemKind='Separator',
                    parentBlock=main.ExperimentalMenu)

    # Add a menu item to the "Experimental" menu to mount/umount
    MenuItem.update(parcel, "MountMenuItem",
                    blockName="_fuse_LoginMenuItem",
                    title=_(u"Show Sidebar in Finder"),
                    event=mountEvent,
                    eventsForNamedLookup=[mountEvent],
                    parentBlock=main.ExperimentalMenu)

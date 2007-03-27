#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
import application.dialogs.Util as Util
from i18n import MessageFactory
from osaf import messages, pim
from osaf.framework.blocks import Block
from osaf.usercollections import UserCollection
from dialogs import LicenseTask, promptLicense

import evdb, EVDBDialog

_ = MessageFactory("Chandler-EVDBPlugin")

class AddEVDBCollectionEvent(Block.AddToSidebarEvent):
    """
    An event used to add a new EVDBCollection to the sidebar.
    """
    def onNewItem (self):
        keywords = EVDBDialog.GetSearchDictFromDialog()
        
        result = None
        
        while keywords:
            try:
                result = evdb.GetCollectionFromSearch(self.itsView, keywords)
            except evdb.LicenseError:
                if promptLicense():
                    continue
            except Exception, e:
                Util.ok(None, _(u"EVDB Search"),
                _(u"An error occurred while fetching events from EVDB:\n%(error)s\n\nSee chandler.log for details.") % {'error': e})
            else:
                if len(list(result)) == 0:
                    result.delete()
                    result = None
                    Util.ok(None, _(u"EVDB Search"), _(u"No matching events were found."))
            return result


def installParcel(parcel, version=None):

    blocks = schema.ns('osaf.framework.blocks', parcel)
    main   = schema.ns('osaf.views.main', parcel)

    # Add an event for creating new EVDB collections
    NewEVDBCollectionEvent = AddEVDBCollectionEvent.update(
        parcel, 'NewEVDBCollectionEvent',
        blockName = 'newEVDBCollectionEvent')

    # Add a separator to the "Experimental" menu ...
    blocks.MenuItem.update(parcel, 'EVDBParcelSeparator',
                           blockName = 'EVDBParcelSeparator',
                           menuItemKind = 'Separator',
                           parentBlock = main.ExperimentalMenu)

    # ... and, below it, a menu item to subscribe to an EVDB
    # calendar.
    blocks.MenuItem.update(parcel, "NewEVDBCollection",
        blockName = "NewEVDBCollectionMenu",
        title = _(u"Subscribe to EVDB Calendar"),
        event = NewEVDBCollectionEvent,
        eventsForNamedLookup = [NewEVDBCollectionEvent],
        parentBlock = main.ExperimentalMenu,
    )

    LicenseTask(None).run()

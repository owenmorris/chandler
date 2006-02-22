from application import schema
import application.dialogs.Util as Util
from i18n import OSAFMessageFactory as _
from osaf import messages, pim
from osaf.framework.blocks import Block

import evdb, EVDBDialog

class EVDBCollection(pim.ListCollection):
    schema.kindInfo(displayName=u"Collection of events from EVDB")
    
    def onAddToCollection(self, event):
        keywords = EVDBDialog.GetSearchDictFromDialog()
        
        result = None
        
        if keywords:
            try:
                result = evdb.GetCollectionFromSearch(self.itsView, keywords)
            except Exception, e:
                Util.ok(None, _(u"EVDB Search"), _(u"An error occurred while fetching events from EVDB:\n%s\n\nSee chandler.log for details." % (e,)))
            else:
                if len(list(result)) == 0:
                    Util.ok(None, _(u"EVDB Search"), _(u"No matching events were found."))
            return result


def installParcel(parcel, version=None):

    # Make a template, which we'll copy whenever creating
    # new collections in the sidebar.
    EVDBCollectionTemplate = EVDBCollection.update(
        parcel, 'EVDBCollectionTemplate',
        displayName = messages.UNTITLED)

    blocks = schema.ns('osaf.framework.blocks', parcel)
    main   = schema.ns('osaf.views.main', parcel)
    detail = schema.ns('osaf.framework.blocks.detail', parcel)

    # Add an event for creating new EVDB collections
    NewEVDBCollectionEvent = Block.ModifyCollectionEvent.update(
        parcel, 'NewEVDBCollectionEvent',
        methodName='onModifyCollectionEvent',
        copyItems = True,
        disambiguateDisplayName = True,
        dispatchToBlockName = 'MainView',
        selectInBlockNamed = 'Sidebar',
        items=[EVDBCollectionTemplate],
        dispatchEnum = 'SendToBlockByName',
        commitAfterDispatch = True)


    # Add a separator to the "Collection" menu ...
    blocks.MenuItem.update(parcel, 'EVDBParcelSeparator',
                           blockName = 'EVDBParcelSeparator',
                           menuItemKind = 'Separator',
                           parentBlock = main.CollectionMenu)

    # ... and, below it, a menu item to subscribe to an EVDB
    # calendar.
    blocks.MenuItem.update(parcel, "NewEVDBCollection",
        blockName = "NewEVDBCollectionMenu",
        title = _(u"Subscribe to EVDB Calendar"),
        event = NewEVDBCollectionEvent,
        eventsForNamedLookup = [NewEVDBCollectionEvent],
        parentBlock = main.CollectionMenu,
    )

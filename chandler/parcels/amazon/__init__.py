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


from AmazonKinds import AmazonCollection, AmazonItem
from AmazonBlocks import AmazonController, AmazonDetailBlock

from application import schema
from osaf.framework.blocks.detail import makeSubtree
from i18n import OSAFMessageFactory as _
from osaf.pim.structs import SizeType, RectType

def installParcel(parcel, version=None):

    controller = AmazonController.update(parcel, "controller")

    blocks = schema.ns('osaf.framework.blocks', parcel)
    main   = schema.ns('osaf.views.main', parcel)
    detail = schema.ns('osaf.framework.blocks.detail', parcel)

    blocks.MenuItem.update(parcel, 'AmazonParcelSeparator',
                           blockName = 'AmazonParcelSeparator',
                           menuItemKind = 'Separator',
                           parentBlock = main.CollectionMenu)

    blocks.MenuItem.update(parcel, "NewAmazonCollection",
        blockName = "NewAmazonCollectionMenu",
        title = _(u"Amazon Keyword Search"),
        event = blocks.BlockEvent.update(parcel, "NewAmazonCollectionEvent",
            blockName = "NewAmazonCollection",
            dispatchEnum = "SendToBlockByReference",
            destinationBlockReference = controller,
            commitAfterDispatch = True,
        ),
        eventsForNamedLookup = [parcel["NewAmazonCollectionEvent"]],
        parentBlock = main.CollectionMenu,
    )

    blocks.MenuItem.update(parcel, "NewAmazonWishList",
        blockName = "NewAmazonWishListMenu",
        title = _(u"Amazon Wish List Search"),
        event = blocks.BlockEvent.update(parcel, "NewAmazonWishListEvent",
            blockName = "NewAmazonWishList",
            dispatchEnum = "SendToBlockByReference",
            destinationBlockReference = controller,
            commitAfterDispatch = True,
        ),
        eventsForNamedLookup = [parcel["NewAmazonWishListEvent"]],
        parentBlock = main.CollectionMenu,
    )

    makeSubtree(parcel, AmazonItem, [
        detail.MarkupBar,
        AmazonDetailBlock.update(parcel, "amazonDetail",
            blockName = "amazonDetail",
            size = SizeType(100,50),
            minimumSize = SizeType(100,50),
        ),
    ])

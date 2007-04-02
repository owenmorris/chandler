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

from datetime import timedelta

from AmazonKinds import AmazonCollection, AmazonItem, DisplayNamesItem
from AmazonBlocks import AmazonController, AmazonDetailBlock
from AmazonDialog import LicenseTask

from application import schema
from osaf.views.detail import makeSubtree
from osaf.startup import PeriodicTask
from osaf.pim.structs import SizeType, RectType
from i18n import MessageFactory

_ = MessageFactory("Chandler-AmazonPlugin")


def installParcel(parcel, version=None):

    controller = AmazonController.update(parcel, "controller")

    blocks = schema.ns('osaf.framework.blocks', parcel)
    main   = schema.ns('osaf.views.main', parcel)
    detail = schema.ns('osaf.views.detail', parcel)

    amazonMenu = blocks.Menu.update(parcel, 'AmazonDemoMenu',
                                    blockName = 'AmazonDemoMenu',
                                    title = _(u'Amazon'),
                                    helpString = _(u'Download wishlists from Amazon'),
                                    childrenBlocks = [ ],
                                    parentBlock = main.ExperimentalMenu)

    blocks.MenuItem.update(parcel, "NewAmazonCollection",
        blockName = "NewAmazonCollectionMenu",
        title = _(u"Amazon Keyword Search..."),
        event = blocks.BlockEvent.update(parcel, "NewAmazonCollectionEvent",
            blockName = "NewAmazonCollection",
            dispatchEnum = "SendToBlockByReference",
            destinationBlockReference = controller,
            commitAfterDispatch = True,
        ),
        eventsForNamedLookup = [parcel["NewAmazonCollectionEvent"]],
        parentBlock = amazonMenu,
    )

    blocks.MenuItem.update(parcel, "NewAmazonWishList",
        blockName = "NewAmazonWishListMenu",
        title = _(u"Amazon Wish List Search..."),
        event = blocks.BlockEvent.update(parcel, "NewAmazonWishListEvent",
            blockName = "NewAmazonWishList",
            dispatchEnum = "SendToBlockByReference",
            destinationBlockReference = controller,
            commitAfterDispatch = True,
        ),
        eventsForNamedLookup = [parcel["NewAmazonWishListEvent"]],
        parentBlock = amazonMenu,
    )

    makeSubtree(parcel, AmazonItem, [
        detail.MarkupBar,
        AmazonDetailBlock.update(parcel, "amazonDetail",
            blockName = "amazonDetail",
            size = SizeType(100,50),
            minimumSize = SizeType(100,50),
        ),
    ])

    DisplayNamesItem.update(parcel, "displayNames",
        namesDictionary = {'ProductName': _(u'Product Name'),
                           'ProductDescription': _(u'Product Description'),
                           'Author': _(u'Author(s)'),
                           'Media': _(u'Media'),
                           'ReleaseDate': _(u'Release Date'),
                           'ImageURL': _(u'image path'),
                           'ProductURL': _(u'product url'),
                           'NewPrice': _(u'New Price'),
                           'UsedPrice': _(u'Used Price'),
                           'Availability': _(u'Availability'),
                           'Manufacturer': _(u'Manufacturer'),
                           'AverageCustomerRating': _(u'Average Customer Review'),
                           'NumberOfReviews': _(u'Number of people who reviewed the item')})

    PeriodicTask.update(parcel, "licenseTask",
                        invoke="amazon.LicenseTask",
                        interval=timedelta(days=1),
                        run_at_startup=True)
    LicenseTask(None).run()

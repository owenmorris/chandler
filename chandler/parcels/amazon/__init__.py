from AmazonKinds import AmazonCollection, AmazonItem
from AmazonBlocks import AmazonController, ImageBlock

from application import schema
from i18n import OSAFMessageFactory as _
from osaf.framework.types.DocumentTypes import SizeType, RectType

def installParcel(parcel, version=None):

    controller = AmazonController.update(parcel, "controller")

    blocks = schema.ns('osaf.framework.blocks', parcel)
    main   = schema.ns('osaf.views.main', parcel)
    detail = schema.ns('osaf.framework.blocks.detail', parcel)
    
    blocks.MenuItem.update(parcel, "NewAmazonCollection",
        blockName = "NewAmazonCollectionMenu",
        title = _(u"New Amazon Collection"),
        event = blocks.BlockEvent.update(parcel, "NewAmazonCollectionEvent",
            blockName = "NewAmazonCollection",
            dispatchEnum = "SendToBlockByReference",
            destinationBlockReference = controller,
            commitAfterDispatch = True,
        ),
        eventsForNamedLookup = [parcel["NewAmazonCollectionEvent"]],
        parentBlock = main.NewItemMenu,
    )
    
    blocks.MenuItem.update(parcel, "NewAmazonWishList",
        blockName = "NewAmazonWishListMenu",
        title = _(u"New Amazon Wish List"),
        event = blocks.BlockEvent.update(parcel, "NewAmazonWishListEvent",
            blockName = "NewAmazonWishList",
            dispatchEnum = "SendToBlockByReference",
            destinationBlockReference = controller,
            commitAfterDispatch = True,
        ),
        eventsForNamedLookup = [parcel["NewAmazonWishListEvent"]],
        parentBlock = main.NewItemMenu,
    )

    detail.DetailTrunkSubtree.update(parcel, "amazon_detail_view",
        key = AmazonItem.getKind(parcel.itsView),
        rootBlocks = [
            detail.MarkupBar,
            detail.DetailSynchronizedLabeledTextAttributeBlock.update(
                parcel, "ProductArea",
                position = 1,
                viewAttribute = "ProductName",
                stretchFactor = 0,
                childrenBlocks = [
                    detail.StaticRedirectAttributeLabel.update(
                        parcel, "AuthorLabel",
                        title = u"author",
                        characterStyle = blocks.LabelStyle,
                        stretchFactor = 0.0,
                        textAlignmentEnum = "Right",
                        minimumSize = SizeType(70, 24),
                        border = RectType(0.0, 0.0, 0.0, 5.0),
                    ),
                    detail.StaticRedirectAttribute.update(
                        parcel, "AuthorAttribute",
                        title = u"about",
                        characterStyle = blocks.LabelStyle,
                        stretchFactor = 0.0,
                        textAlignmentEnum = "Left",
                    ),
                ],
            ),
            ImageBlock.update(parcel, "image",
                blockName = "product image",
                size = SizeType(100,50),
                minimumSize = SizeType(100,50),
            ),
        ],
    )


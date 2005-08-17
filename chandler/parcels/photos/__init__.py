from Photos import PhotoMixin, Photo
from application import schema

def installParcel(parcel, old_version=None):

    blocks = schema.ns('osaf.framework.blocks', parcel)
    detail = schema.ns('osaf.framework.blocks.detail', parcel)

    detail.DetailTrunkSubtree.update(parcel, "photo_subtree",
        key = PhotoMixin.getKind(parcel.itsView),
        rootBlocks = [
            detail.DetailSynchronizedAttributeEditorBlock.update(
                parcel, "photo_image",
                viewAttribute = "photoBody",
                position = 0.86,
                stretchFactor = 1.0,
                border = blocks.RectType(2.0, 2.0, 2.0, 2.0),
                presentationStyle = blocks.PresentationStyle.update(
                    parcel, "photo_image_presentation",
                    format = "Image"
                )
            )
        ]
    )

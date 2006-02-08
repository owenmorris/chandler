from Photos import PhotoMixin, Photo
from application import schema
from osaf.pim.structs import RectType
from osaf.framework.blocks.detail import makeSubtree

def installParcel(parcel, old_version=None):
    blocks = schema.ns('osaf.framework.blocks', parcel)
    detail = schema.ns('osaf.framework.blocks.detail', parcel)

    makeSubtree(parcel, PhotoMixin, [
        detail.DetailSynchronizedAttributeEditorBlock.update(
            parcel, "photo_image",
            viewAttribute = u"photoBody",
            position = 0.86,
            stretchFactor = 1.0,
            border = RectType(2.0, 2.0, 2.0, 2.0),
            presentationStyle = blocks.PresentationStyle.update(
                parcel, "photo_image_presentation",
                format = "Image"
            )
        )])

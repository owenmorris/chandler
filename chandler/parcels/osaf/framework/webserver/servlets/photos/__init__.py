from application import schema
from osaf.contentmodel import Notes

class PhotoMixin(schema.Item):

    schema.kindInfo(displayName = "Photo Mixin")

    caption = schema.One(schema.String)
    about = schema.One(redirectTo = 'caption')
    date = schema.One(redirectTo = 'dateTaken')
    file = schema.One(schema.String)
    dateTaken = schema.One(schema.DateTime)

    schema.addClouds(
        sharing = schema.Cloud(caption,dateTaken)
    )

class Photo(PhotoMixin, Notes.Note):
    schema.kindInfo(displayName = "Photo")
    
del schema, Notes   # don't leave these around for accidental import by others
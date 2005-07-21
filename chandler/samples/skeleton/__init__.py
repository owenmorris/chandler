from application import schema
from osaf.contentmodel import ContentItem

class MyKind1(ContentItem):
    """An example content kind"""
    
    attr1 = schema.One(schema.String, displayName="Attribute 1")
   
    schema.kindInfo(
        displayName = "Example Kind"
    )

    # redirection attributes
    who = schema.Role(redirectTo="attr1")

    attr2 = schema.One(schema.String, displayName="Attribute 2")
  
    # Typical clouds include a "copying" cloud, and a "sharing" cloud

    schema.addClouds(
        sharing = schema.Cloud(attr1, attr2)
    )

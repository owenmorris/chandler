from application import schema
from osaf import pim

class MyKind1(pim.ContentItem):
    """An example content kind"""
    
    attr1 = schema.One(schema.Text, displayName=u"Attribute 1")
   
    schema.kindInfo(
        displayName = u"Example Kind"
    )

    # redirection attributes
    who = schema.Descriptor(redirectTo="attr1")

    attr2 = schema.One(schema.Text, displayName=u"Attribute 2")
  
    # Typical clouds include a "copying" cloud, and a "sharing" cloud

    schema.addClouds(
        sharing = schema.Cloud(attr1, attr2)
    )

def installParcel(parcel, oldVersion=None):
    # create an instance of MyKind, named 'anItem', in the parcel
    MyKind1.update(
        parcel, "anItem",
        attr1 = "Setting custom attributes is simple",
    )


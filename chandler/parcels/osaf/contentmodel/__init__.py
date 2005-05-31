# contentmodel parcel module

# Define ContentModel to be our custom parcel class
from ContentModel import ContentModel as __parcel_class__

# Import classes whose schemas are part of this parcel
# (this will eventually include all ContentItem subclasses in
# this package)
from ContentModel import ContentItem
from contacts.Contacts import Contact

# Import ItemCollection class under another name, so it doesnt't
# clash with the ItemCollection *module*.  The schema API and parcel
# loader will still know its true name is ItemCollection, even though
# it's imported under an alias
from ItemCollection import ItemCollection as __ItemCollection


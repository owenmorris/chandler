
from Detail import *
from osaf.framework.blocks import *
from osaf.pim.item_collections import ItemCollection

def installParcel(parcel, oldVersion=None):
    # Declare the detail view's attribute editors at repository-init time
    # If you edit this dictionary, please keep it in alphabetical order by key.
    aeList = {
        'DateTime+calendarDateOnly': 'CalendarDateAttributeEditor',
        'DateTime+calendarTimeOnly': 'CalendarTimeAttributeEditor',
        'EmailAddress+outgoing': 'OutgoingEmailAddressAttributeEditor',
        'RecurrenceRuleSet+custom': 'RecurrenceCustomAttributeEditor',
        'RecurrenceRuleSet+ends': 'RecurrenceEndsAttributeEditor',
        'RecurrenceRuleSet+occurs': 'RecurrenceAttributeEditor',
        'TimeDelta+reminderPopup': 'ReminderDeltaAttributeEditor',
    }
    for typeName, className in aeList.items():
        AttributeEditorMapping.update(parcel, typeName, className=\
                                      __name__ + '.' + className)

    # The detail view is notified of changes in the single item we stick
    # into this item collection
    dvSelectedItemCollection = \
        ItemCollection.update(parcel, 'DetailViewSelectedItemCollection',
                              displayName=_(u'DetailViewSelectedItemCollection'),
                              _rule="")
    
    ##
    ## Declare our blocks
    ##
    
    # The DetailTrunkCache starts each specific DetailTrunk by cloning this stub.
    detailRoot = DetailRootBlock.template('DetailRoot',
                                          orientationEnum='Vertical',
                                          size=SizeType(80, 20),
                                          minimumSize=SizeType(80, 40),
                                          eventBoundary=True,
                                          contents=dvSelectedItemCollection)
    detailRoot.install(parcel)

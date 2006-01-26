from SideBar import SidebarBlock
from SideBar import CPIATestSidebarBPBDelegate, SidebarBPBDelegate


def installParcel(parcel, oldVersion=None):
    from events import makeMainEvents
    from menus import makeMainMenus
    from mainblocks import makeMainView 
    from summaryblocks import makeSummaryBlocks

    makeMainEvents (parcel)
    makeMainMenus (parcel)
    makeMainView (parcel)
    makeSummaryBlocks (parcel)
    
    from osaf.framework import prompts

    prompts.DialogPref.update(parcel, "clearCollectionPref")


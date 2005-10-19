from SideBar import SidebarBlock
from SideBar import CPIATestSidebarTrunkDelegate, SidebarTrunkDelegate


def installParcel(parcel, oldVersion=None):
    from mainblocks import make_mainview
    from summaryblocks import make_summaryblocks
    make_mainview(parcel)
    make_summaryblocks(parcel)
    

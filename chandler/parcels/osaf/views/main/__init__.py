from SideBar import SidebarBlock as __SidebarBlock
from SideBar import CPIATestSidebarTrunkDelegate, SidebarTrunkDelegate

from mainblocks import make_mainview
from summaryblocks import make_summaryblocks

def installParcel(parcel, oldVersion=None):
    make_mainview(parcel)
    make_summaryblocks(parcel)
    

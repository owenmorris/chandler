from SideBar import SidebarBlock as __SidebarBlock
from SideBar import CPIATestSidebarTrunkDelegate, SidebarTrunkDelegate

from mainblocks import make_mainview

def installParcel(parcel, oldVersion=None):
    make_mainview(parcel)
    

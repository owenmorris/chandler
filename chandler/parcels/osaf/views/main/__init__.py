#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from Sections import SectionedGridDelegate
from SideBar import SidebarBlock, CPIATestSidebarBranchPointDelegate, SidebarBranchPointDelegate

from Dashboard import DashboardPrefs

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

    DashboardPrefs.update(parcel, "dashboardPrefs")

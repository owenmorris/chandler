

def installParcel(parcel, oldVersion=None):
    from osaf.views.main.menus import makeMainMenus
    from mainblocks import makeCPIATestMainView

    makeMainMenus (parcel)
    makeCPIATestMainView(parcel)
    

__version__ = "$Revision: 6708 $"
__date__ = "$Date: 2005-08-19 17:29:03 -0700 (Fri, 19 Aug 2005) $"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from CPIAScript import *
import application.schema as schema
import os

__all__ = [
    HotkeyScript, RunScript, RunStartupScript, Script, EventTiming
]

def installParcel(parcel, oldVersion=None):
    blocks = schema.ns('osaf.framework.blocks', parcel)
    main   = schema.ns('osaf.views.main', parcel)
    detail = schema.ns('osaf.framework.blocks.detail', parcel)
    pim = schema.ns("osaf.pim", parcel)
    app = schema.ns("osaf.app", parcel)
    contacts = schema.ns("osaf.pim.contacts", parcel)
    scripting = schema.ns("osaf.framework.scripting", parcel)
    
    # reference to OSAF Development contact
    OsafDev = app.OSAFContact

    # Scripts:
    # The app test script is in osaf.app

    Script.update(parcel, "Script F2 - Create a New Script",
                  creator = OsafDev,
                  bodyString=scripting.ScriptFile(
                      os.path.join(os.path.dirname(__file__),
                                   "Sample_NewScript.py"))
                  )

    Script.update(parcel, "Script F3 - Event timing example",
                  creator = OsafDev,
                  bodyString=scripting.ScriptFile(
                      os.path.join(os.path.dirname(__file__),
                                   "Sample_EventTiming.py"))
                  )

    # UI Elements:
    # -----------

    # "Scripts" Set
    scriptsSetRule = "for i inevery '//parcels/osaf/framework/scripting/Script' where True"
    scriptsSet = pim.ItemCollection.update(parcel, "ScriptsItemCollection",
                                           displayName = "Scripts",
                                           renameable = False,
                                           _rule = scriptsSetRule
                                           )
    
    # Event to put "Scripts" in the Sidebar
    addScriptsEvent = blocks.ModifyContentsEvent.update(parcel, "AddScriptsCollectionEvent",
                                                        blockName = "AddScriptsCollectionEvent",
                                                        dispatchEnum = "SendToBlockByName",
                                                        dispatchToBlockName = "Sidebar",
                                                        methodName = "onModifyContentsEvent",
                                                        items = [scriptsSet], 
                                                        selectFirstItem=True,
                                                        copyItems=True,
                                                        commitAfterDispatch = True
                                                        )

    # Menu item to put "Scripts" in the Sidebar
    blocks.MenuItem.template("AddScriptsCollectionMenu",
                           title = "Add Scripts to Sidebar",
                           event = addScriptsEvent,
                           parentBlock = main.TestMenu
                           ).install(parcel)
    
    # Block Subtree for the Detail View of a Script
    # ------------
    detail.DetailTrunkSubtree.update(parcel, 'script_detail_view',
                                     key=scripting.Script.getKind(parcel.itsView),
                                     rootBlocks=[
                                         detail.makeSpacer(parcel, height=6, position=0.01).install(parcel),
                                         detail.HeadlineArea,
                                         detail.makeSpacer(parcel, height=7, position=0.8).install(parcel),
                                         detail.NotesBlock
                                         ])      

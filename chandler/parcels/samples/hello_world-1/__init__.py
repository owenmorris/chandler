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


import application.schema as schema
import osaf.framework.attributeEditors as attributeEditors
import osaf.framework.blocks as blocks
from osaf.pim.structs import RectType, SizeType
from hello_world import MP3

def installParcel(parcel, oldVersion=None):

    repositoryView = parcel.itsView
    blocksParcel = schema.ns('osaf.framework.blocks', repositoryView)
    
    aePresentationStyle = blocks.ControlBlocks.PresentationStyle.update(
        parcel, 'presentationStyle',
        format = 'static')

    attributeEditorBlock = blocks.ControlBlocks.AEBlock.update(
        parcel, 'attributeEditorBlock',
        blockName = 'HeadlineBlock',
        alignmentEnum = 'alignTopCenter',
        viewAttribute = 'displayName',
        presentationStyle = aePresentationStyle)
    
    button = blocks.ControlBlocks.Button.update(
        parcel, 'button',
        minimumSize = SizeType (40, 20),
        alignmentEnum = 'alignTopLeft',
        stretchFactor = 0.0,
        title = u'Play')
        
    view = blocks.BoxContainer.update(
        parcel, 'HelloWorldBoxContainer',
        orientationEnum = 'Horizontal',
        eventBoundary = True,
        childrenBlocks=[button, attributeEditorBlock])
    
    blocks.BranchPoint.ViewableKind(MP3.getKind(repositoryView)).detailView = view

    song = MP3.update(parcel, "French Rock",
                      about = "French Rock")
    
    #eventually we need to populate the song using:
    #stream = song.audio.getOutputStream()
    #stream.write

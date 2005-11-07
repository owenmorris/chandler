import application.schema as schema
import osaf.framework.attributeEditors as attributeEditors
import osaf.framework.blocks as blocks
from osaf.framework.types.DocumentTypes import RectType, SizeType
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
        viewAttribute = 'about',
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
    
    blocks.Trunk.ViewableKind(MP3.getKind(repositoryView)).detailView = view

    song = MP3.update(parcel, "French Rock",
                      about = "French Rock")
    
    #eventually we need to populate the song using:
    #stream = song.audio.getOutputStream()
    #stream.write
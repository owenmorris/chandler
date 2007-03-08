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


__parcel__ = "photos"

from Photos import Photo, PhotoMixin, NewImageEvent
from application import schema
from osaf.pim.structs import RectType
from osaf.pim.notes import Note
from osaf.views.detail import makeSubtree, makeEditor
from osaf.framework.blocks.MenusAndToolbars import MenuItem
from i18n import MessageFactory

_ = MessageFactory("Chandler-PhotoPlugin")

def installParcel(parcel, old_version=None):
    blocks = schema.ns('osaf.framework.blocks', parcel)

    makeSubtree(parcel, PhotoMixin, [
        makeEditor(parcel, "PhotoBody",
            viewAttribute=u"photoBody",
            stretchFactor=1.0,
            border=RectType(2.0, 2.0, 2.0, 2.0),
            position=0.86,           
            presentationStyle = { 'format': 'Image' }
        ).install(parcel)
    ])

    # Event to add a new image to the repository
    newImageEvent = NewImageEvent.update(
        parcel, 'NewImage',
        blockName = 'NewImage',
        classParameter = Note,
        allCollection = schema.ns('osaf.pim', parcel.itsView).allCollection)

    # Add menu item to Chandler
    MenuItem.update(
        parcel, 'ImportImageItem',
        blockName = 'ImportImageItemMenuItem',
        title = _(u'Import an image from disk'),
        helpString = _(u'Import an image from disk'),
        event = newImageEvent,
        eventsForNamedLookup = [newImageEvent],
        parentBlock = schema.ns('osaf.views.main', parcel).ImportExportMenu)
 

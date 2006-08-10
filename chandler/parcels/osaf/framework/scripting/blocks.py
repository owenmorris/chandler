#   Copyright (c) 2005-2006 Open Source Applications Foundation
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


"""
This file provides block instances for the detail view
"""

import wx
import os, sys
from i18n import ChandlerMessageFactory as _

from application import schema
from osaf.framework.blocks.detail import Detail
from osaf.framework.blocks import ControlBlocks
from osaf.framework.attributeEditors import AttributeEditors
from application.dialogs import Util
from osaf.framework.blocks import Block

def installBlocks(parcel, oldVersion=None):
    from osaf.pim import structs
    from script import Script

    detail = schema.ns('osaf.framework.blocks.detail', parcel)
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)

    # UI Elements:
    # -----------
    hotkeyArea = detail.makeArea(parcel, 'HotkeyArea',
                            position=0.6,
                            childrenBlocks=[
                                detail.makeLabel(parcel, _(u'Hotkey'), borderTop=4),
                                detail.makeSpacer(parcel, width=6),
                                detail.makeEditor(parcel, 'EditFKey',
                                           viewAttribute=u'fkey',
                                           stretchFactor=0.0,
                                           size=structs.SizeType(75, -1)),
                                detail.makeSpacer(parcel, width=60),
                                ]).install(parcel)

    saveFileEvent = Block.BlockEvent.template('SaveFile',
                                              dispatchEnum='SendToSender',
                                              ).install(parcel)

    openFileButton = OpenFileButton.template('openFileButton',
                                             title=_(u'Open'),
                                             buttonKind='Text',
                                             characterStyle=blocks.LabelStyle,
                                             stretchFactor=0.0,
                                             size=structs.SizeType(100, -1),
                                             event=saveFileEvent
                                             ).install(parcel)

    saveFileButton = SaveFileButton.template('saveFileButton',
                                             title=_(u'Save'), 
                                             buttonKind='Text',
                                             characterStyle=blocks.LabelStyle,
                                             stretchFactor=0.0,
                                             size=structs.SizeType(100, -1),
                                             event=saveFileEvent
                                             ).install(parcel)

    saveAsFileButton = SaveAsFileButton.template('saveAsFileButton',
                                             title=_(u'Save As'), # fill in title later
                                             buttonKind='Text',
                                             characterStyle=blocks.LabelStyle,
                                             stretchFactor=0.0,
                                             size=structs.SizeType(100, -1),
                                             event=saveFileEvent
                                             ).install(parcel)

    testCheckboxArea = detail.makeArea(parcel, 'TestCheckboxArea',
                            position=0.7,
                            childrenBlocks=[
                                detail.makeLabel(parcel, _(u'test'), borderTop=4),
                                detail.makeSpacer(parcel, width=6),
                                detail.makeEditor(parcel, 'EditTest',
                                           viewAttribute=u'test',
                                           stretchFactor=0.0,
                                           minimumSize=structs.SizeType(16,-1)),
                                detail.makeSpacer(parcel, width=6),
                                openFileButton, saveFileButton, saveAsFileButton,
                                ]).install(parcel)

    scriptTextArea = detail.makeEditor(parcel, 'NotesBlock',
                                       viewAttribute=u'body',
                                       presentationStyle={'lineStyleEnum': 'MultiLine',
                                                          'format': 'fileSynchronized'},
                                       position=0.9).install(parcel)

    filePathArea = detail.makeArea(parcel, 'FilePathArea',
                                   baseClass=FilePathAreaBlock,
                                   position=0.8,
                                   childrenBlocks=[
                                       detail.makeLabel(parcel, _(u'path'), borderTop=4),
                                       detail.makeSpacer(parcel, width=6),
                                       detail.makeEditor(parcel, 'EditFilePath',
                                                         viewAttribute=u'filePath',
                                                         presentationStyle={'format': 'static'}
                                                         )
                                       ]).install(parcel)


    # Block Subtree for the Detail View of a Script
    # ------------
    detail.makeSubtree(parcel, Script, [
        detail.makeSpacer(parcel, height=6, position=0.01).install(parcel),
        detail.HeadlineArea,
        hotkeyArea,
        testCheckboxArea,
        filePathArea,
        detail.makeSpacer(parcel, height=7, position=0.8).install(parcel),
        scriptTextArea
    ])

    AttributeEditors.AttributeEditorMapping.update(parcel, 
                                                   'Text+fileSynchronized',
                                                   className=__name__ + '.' +
                                                   'FileSynchronizedAttributeEditor')

"""
Support classes
"""
class FileSynchronizedAttributeEditor(AttributeEditors.StringAttributeEditor):
    """
    Delegate for an Attribute Editor that synchronizes the attribute with
    a file's contents.
    """
    def BeginControlEdit (self, item, attributeName, control):
        """ 
        Prepare to edit this value. 
        """
        # sync first, then we'll have the right value
        item.sync_file_with_model()
        return super(FileSynchronizedAttributeEditor, self).BeginControlEdit(item, attributeName, control)

    def SetAttributeValue (self, item, attributeName, value):
        """ Set the value of the attribute given by the value. """
        # has the data really changed?
        if value != self.GetAttributeValue(item, attributeName):
            # update the model data
            super(FileSynchronizedAttributeEditor, 
                         self).SetAttributeValue(item, attributeName, value)
            # update the file data too
            item.sync_file_with_model()

class FilePathAreaBlock(Detail.DetailSynchronizedContentItemDetail):
    """
    Block to show (or hide) the File Path area of the script.
    """
    def shouldShow(self, item):
        return len(item.filePath) > 0

class OpenFileButton(Detail.DetailSynchronizer, ControlBlocks.Button):
    """
    Block to show (or hide) the "Open File" button, and
    to handle that event.
    """
    def shouldShow(self, item):
        self._item = item
        return len(item.body) == 0

    def onSaveFileEvent(self, event):
        """
        Open a file to associate with this script, or save an existing
        script to a file.
        """
        if not self._item.body:
            # no script body, open and overwrite existing model data
            title = _(u"Open a script file")
            message = _(u"Open an existing script file, or choose a name\n"
                        "for a new file for this script.")
            flags = wx.OPEN
        else:
            # model data exists, we need a place to write it
            title =_(u"Save this script file as")
            message = _(u"Choose an existing script file, or enter a name\n"
                        "for a new file for this script.")
            flags = wx.SAVE | wx.OVERWRITE_PROMPT

        if self._item.filePath:
            # already have a file, default to that name and path
            # dirname returns unicode here since the filePath variable is unicode
            path = os.path.dirname(self._item.filePath)
            name = self._item.filePath.split(os.sep)[-1]
        else:
            # no file yet, point to scripts directory, use display name
            name = self._item.displayName+u".py"
            # dirname returns an str of bytes since the __file__ variable is bytes
            path = os.path.dirname(schema.ns('osaf.app', self).scripts.__file__)
            # convert the path bytes to unicode
            path = unicode(path, sys.getfilesystemencoding())

        # present the Open/Save dialog
        result = Util.showFileDialog(wx.GetApp().mainFrame, 
                                     title,
                                     path,
                                     name,
                                     _(u"Python files|*.py|") + _(u"All files (*.*)|*.*"),
                                     flags)
        cmd, dir, fileName = result

        if cmd == wx.ID_OK:
            preferFile = len(self._item.body) == 0
            writeFile = not preferFile
            self._item.filePath = os.path.join(dir, fileName)
            self._item.sync_file_with_model(preferFile=preferFile)
            resyncEvent = schema.ns('osaf.framework.blocks.detail', self).Resynchronize
            Block.Block.post(resyncEvent, {}, self)
            self.postEventByName('ResyncDetailParent', {})

class SaveFileButton(OpenFileButton):
    """
    Block to show (or hide) the "Save" button, and
    to handle that event.
    """
    def shouldShow(self, item):
        self._item = item
        return len(item.body) > 0 and len(item.filePath) == 0

class SaveAsFileButton(OpenFileButton):
    """
    Block to show (or hide) the "Save As" button, and
    to handle that event.
    """
    def shouldShow(self, item):
        self._item = item
        return len(item.body) > 0 and len(item.filePath) > 0
    

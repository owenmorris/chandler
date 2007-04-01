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


from blockviewer import BlockItemDetail
from osaf.framework.blocks import Tree, SplitterWindow, Column
from osaf.pim.structs import SizeType, RectType
from i18n import ChandlerMessageFactory as _
from osaf.framework.blocks import FrameWindow, BoxContainer

def installParcel(parcel, oldName=None):

    FrameWindow.template(
        'BlockViewerFrameWindow',
        size=SizeType(768, 512),
        windowTitle = _(u"Block Viewer"),
        eventBoundary=True,
        childBlocks = [
            SplitterWindow.template(
                'Splitter',
                eventBoundary=True,
                splitPercentage=0.5,
                childBlocks=[
                    Tree.template(
                        'Tree',
                        elementDelegate='osaf.views.blockviewer.blockviewer.BlockDelegate',
                        hideRoot=False,
                        noLines=False,
                        columns = [
                            Column.update(
                                parcel, 'ColumnBlockName',
                                heading='BlockName',
                                width=350),
                            Column.update(
                                parcel, 'ColumnKind',
                                heading='Kind',
                                width=100),
                            Column.update(
                                parcel, 'ColumnWidget',
                                heading='Widget',
                                width=280),
                            Column.update(
                                parcel, 'ColumnUUID',
                                heading='UUID',
                                width=40),
                            ]),
                    
                    BoxContainer.template('BlockItemDetailContainer',
                        border = RectType(4, 0, 0, 0),
                        childBlocks = [
                            BlockItemDetail.template(
                                'BlockItemDetail',
                                size=SizeType(-1,-1))
                            ])
                    ])
            ]).install(parcel)

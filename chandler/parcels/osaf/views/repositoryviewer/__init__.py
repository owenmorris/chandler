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


from Repository import RepositoryItemDetail
from osaf.framework.blocks import Tree, SplitterWindow, Column
from osaf.pim.structs import SizeType, RectType
from i18n import ChandlerMessageFactory as _
from osaf.framework.blocks import FrameWindow, BoxContainer

def installParcel(parcel, oldName=None):

    FrameWindow.template(
        'RepositoryViewerFrameWindow',
        size=SizeType(768, 512),
        windowTitle = _(u"Repository Viewer"),
        eventBoundary=True,
        childrenBlocks = [
            SplitterWindow.template(
                'RepositoryView',
                displayName=u'Repository Viewer',
                eventBoundary=True,
                splitPercentage=0.5,
                childrenBlocks=[
                    Tree.template(
                        'RepositoryTree',
                        elementDelegate='osaf.views.repositoryviewer.Repository.RepositoryDelegate',
                        hideRoot=False,
                        noLines=False,
                            columns = [
                                Column.update(parcel, 'RepositoryViewColItemName',
                                              heading='ItemName',
                                              width=160),
                                Column.update(parcel, 'RepositoryViewColDisplayName',
                                              heading='Display Name',
                                              width=110),
                                Column.update(parcel, 'RepositoryViewColKind',
                                              heading='Kind',
                                              width=70),
                                Column.update(parcel, 'RepositoryViewColUUID',
                                              heading='UUID',
                                              width=245),
                                Column.update(parcel, 'RepositoryViewColPath',
                                              heading='Path',
                                              width=155),
                                ],
                                
                        size=SizeType(600,200),
                        minimumSize=SizeType(400,100)),
                    BoxContainer.template('RepositoryItemDetailContainer',
                        border = RectType(4, 0, 0, 0),
                        childrenBlocks = [
                            RepositoryItemDetail.template('RepositoryItemDetail',
                                                          size=SizeType(-1,-1))
                            ])
                    ])
            ]).install(parcel)


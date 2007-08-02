#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

from application import schema

from osaf.pim import ContentItem, MailStamp, Modification, Stamp
from osaf.sharing import SharedItem

class CommunicationStatus(schema.Annotation):
    """
    Generate a value that expresses the communications status of an item, 
    such that the values can be compared for indexing for the communications
    status column of the Dashboard.

    The sort terms are:
      1. unread, needs-reply, read
      2. Not mail (and no error), sent mail, error, queued mail, draft mail
      3a. If #2 is not mail: created, edited
      3b. If #2 is mail: out, in, other
      4b. If #2 is mail: firsttime, updated
      
    The constants used here map to the dashboard specification for Chandler:
    
    <http://svn.osafoundation.org/docs/trunk/docs/specs/rel0_7/Dashboard-0.7.html#comm-states>
    """
    schema.kindInfo(annotates=ContentItem)

    # These flag bits govern the sort position of each communications state:
    # Terms with set "1"s further left will sort earlier.
    # 1:
    # (unread has neither of these set)
    # NEEDS_REPLY =  1
    # READ        = 1

    # 2:
    # (non-mail has none of these set)
    # SENT        =      1
    # ERROR       =     1
    # QUEUED      =    1
    # DRAFT       =   1

    # 3a:
    # (created has this bit unset)
    # EDITED      =       1

    # 3b:
    # OUT         =          1
    # IN          =         1
    # NEITHER     =        1
    # (NEITHER is also called NEUTRAL in the spec).

    # 4b:
    # (firsttime has this bit unset)
    # UPDATE      =           1


    UPDATE, OUT, IN, NEITHER, EDITED, SENT, ERROR, QUEUED, DRAFT, NEEDS_REPLY, READ = (
        1<<n for n in xrange(11)
    )

    @staticmethod
    def getItemCommState(itemOrUUID, view=None):
        """ Given an item or a UUID, determine its communications state """

        if view is None:
            view = itemOrUUID.itsView
            itemOrUUID = getattr(itemOrUUID, 'proxiedItem', itemOrUUID)

        modifiedFlags, lastMod, stampTypes, fromMe, \
        toMe, needsReply, read, error, conflictingStates = \
            view.findInheritedValues(itemOrUUID,
                                     *CommunicationStatus.attributeValues)

        result = 0

        # error
        if error or conflictingStates:
            result |= CommunicationStatus.ERROR

        if MailStamp in stampTypes:
            # update: This means either: we have just
            # received an update, or it's ready to go
            # out as an update
            modification = Modification
            if (modification.updated == lastMod or
                (modification.sent != lastMod and
                modification.sent in modifiedFlags)):
                result |= CommunicationStatus.UPDATE

            # in, out, neither
            if toMe:
                result |= CommunicationStatus.IN
            if fromMe:
                result |= CommunicationStatus.OUT
            elif not toMe:
                result |= CommunicationStatus.NEITHER

            # queued
            if modification.queued in modifiedFlags:
                result |= CommunicationStatus.QUEUED
            # sent
            if lastMod in (modification.sent, modification.updated):
                result |= CommunicationStatus.SENT
            # draft if it's not one of sent/queued/error
            if  result & (CommunicationStatus.SENT |
                          CommunicationStatus.QUEUED |
                          CommunicationStatus.ERROR) == 0:
                result |= CommunicationStatus.DRAFT
        else:
            # edited
            if Modification.edited in modifiedFlags:
                result |= CommunicationStatus.EDITED

        # needsReply
        if needsReply:
            result |= CommunicationStatus.NEEDS_REPLY

        # read
        if read:
            result |= CommunicationStatus.READ

        return result

    @staticmethod
    def dump(status):
        """
        For debugging (and helpful unit-test messages), explain our flags.
        'status' can be a set of flags, an item, or an item UUID.
        """
        if not isinstance(status, int):
            status = CommunicationStatus.getItemCommState(status)
        if status == 0:
            return "(none)"
        result = [ flagName for flagName in ('UPDATE', 'OUT', 'IN',
                                             'NEITHER', 'EDITED',
                                             'SENT', 'QUEUED', 
                                             'DRAFT', 'NEEDS_REPLY',
                                             'READ')
                   if status & getattr(CommunicationStatus, flagName)]
        return '+'.join(result)

    attributeValues = (
        (ContentItem.modifiedFlags, frozenset()),
        (ContentItem.lastModification, None),
        (Stamp.stamp_types, frozenset()),
        (MailStamp.fromMe, False),
        (MailStamp.toMe, False),
        (ContentItem.needsReply, False),
        (ContentItem.read, False),
        (ContentItem.error, None),
        (SharedItem.conflictingStates, False),
    )
    attributeDescriptors = tuple(t[0] for t in attributeValues)
    attributeValues = tuple((attr.name, val) for attr, val in attributeValues)
    
    status = schema.Calculated(
        schema.Integer,
        basedOn=attributeDescriptors,
        fget=lambda self: self.getItemCommState(self.itsItem),
    )

    def addDisplayWhos(self, whos):
        """
        Add tuples to the "whos" list: (priority, "text", source name)
        """
        commState = CommunicationStatus.getItemCommState(self.itsItem)
        lastModifiedBy = self.itsItem.lastModifiedBy
        if lastModifiedBy is not None:
            lastModifiedBy = lastModifiedBy.getLabel()
            if commState & (CommunicationStatus.EDITED | CommunicationStatus.UPDATE):
                lastMod = self.itsItem.lastModification
                if lastMod == Modification.edited:
                    whos.append((1, lastModifiedBy, 'editor'))
                else:
                    whos.append((1, lastModifiedBy, 'updater'))
            else:
                whos.append((1000, lastModifiedBy, 'creator'))

        stamp_types = Stamp(self.itsItem).stamp_types
        if stamp_types and MailStamp in stamp_types:
            msg = MailStamp(self.itsItem)
            preferFrom = (commState & CommunicationStatus.OUT) == 0            
            toAddress = getattr(msg, 'toAddress', schema.Nil)
            if len(toAddress) > 0:
                toText = u", ".join(x.getLabel() for x in toAddress)
                if len(toText) > 0:
                    whos.append((preferFrom and 4 or 2, toText, 'to'))

            originators = getattr(msg, 'originators', schema.Nil)
            if len(originators) > 0:
                originatorsText = u", ".join(x.getLabel() for x in originators)
                if len(originatorsText) > 0:
                    whos.append((preferFrom and 2 or 3, originatorsText, 'from'))
    
            fromAddress = getattr(msg, 'fromAddress', None)
            if fromAddress is not None:
                fromText = fromAddress.getLabel()
                if len(fromText) > 0:
                    whos.append((preferFrom and 3 or 4, fromText, 'from'))


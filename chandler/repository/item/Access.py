#   Copyright (c) 2004-2006 Open Source Applications Foundation
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


class Permissions(object):

    DENY    = 0x0001
    READ    = 0x0002
    WRITE   = 0x0004
    REMOVE  = 0x0008
    CHANGE  = 0x0010


class AccessDeniedError(Exception):
    pass


class ACL(list):

    def verify(self, principal, perms):

        grant = deny = 0

        for ace in self:
            on, off = ace.verify(principal, perms)
            grant |= on
            deny |= off

        return grant & ~deny


class ACE(object):

    def __init__(self, pid, perms, deny=False):

        super(ACE, self).__init__()

        self.pid = pid
        self.perms = perms

        if deny:
            self.perms |= Permissions.DENY

    def __repr__(self):

        return '<ACE: %s 0x%0.8x>' %(self.pid.str64(), self.perms)

    def verify(self, principal, perms):

        if not principal.isMemberOf(self.pid):
            return (0, 0)

        if self.perms & Permissions.DENY:
            return (0, perms & self.perms)
        else:
            return (perms & self.perms, 0)

warning_banner = """
###########################################################################
# DO NOT DELETE!  The following UUIDs are here for purposes of repository
# synchronization and schema evolution.  If you delete them, you will have
# difficulty upgrading databases created with this schema.  If you rename
# items in the code above, you must rename them here as well, and if you
# move items to another module, you must move their UUIDs with them.  In
# other words, once a UUID is assigned to a particular role, entity,
# relationship, or module, it should move with the module.
###########################################################################

"""

try:
    from chandlerdb.util.UUID import UUID as make_uuid
except ImportError:
    try:
        from peak.util.uuid import UUID as make_uuid
    except ImportError:
        def make_uuid():
            raise NotImplementedError("Could not find a UUID library")

from spike.schema import Role, Activator

class UUIDGenerator:
    def __init__(self,make_uuid=make_uuid):
        self.make_uuid = make_uuid
        self.memo = {}

    def genClass(self,cls):
        if cls not in self.memo:
            self.memo[cls] = True
            if not cls.uuid:
                yield "%s.uuid = %r\n" % (cls.__name__, str(self.make_uuid()))
            for item in cls.__dict__.values():
                if isinstance(item,Role) and item.owner is cls:
                    for line in self.genRole(item):
                        yield line

    def genRole(self,role):
        if role not in self.memo:
            self.memo[role] = True
            if not role.uuid:
                yield "%s.%s.uuid = %r\n" % (
                    role.owner.__name__, role.name, str(self.make_uuid())
                )
            if role.inverse is not None and role.inverse.owner is None:
                if not role.inverse.uuid:
                    yield "%s.%s.inverse.uuid = %r\n" % (
                        role.owner.__name__, role.name, str(self.make_uuid())
                    )       
                

    def genMapping(self,mdict):
        if 'uuid' not in mdict:
            yield "uuid = %r\n" % str(self.make_uuid())
        modname = mdict.get('__name__')
        for v in mdict.values():
            if isinstance(v,Activator) and v.__module__==modname:
                for line in self.genClass(v):
                    yield line

    def fromSource(self,source):
        mdict = dict(__name__=None)
        exec source in mdict
        trailer = ''.join(self.genMapping(mdict))
        if trailer and warning_banner not in source:
            trailer = warning_banner+trailer
        return trailer


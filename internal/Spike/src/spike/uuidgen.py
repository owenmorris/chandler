"""UUID Generation utitilies -- see ``uuidgen.txt`` for documentation"""

try:
    from chandlerdb.util.UUID import UUID as make_uuid
except ImportError:
    try:
        from peak.util.uuid import UUID as make_uuid
    except ImportError:
        def make_uuid():
            raise NotImplementedError("Could not find a UUID library")

from spike.schema import Role, Activator
import sys, getopt

__all__ = ['UUIDGenerator', 'main']


warning_banner = """
###########################################################################
# DO NOT DELETE!  The following UUIDs are here for purposes of repository
# synchronization and schema evolution.  If you delete them, you will have
# difficulty upgrading databases created with this schema.  If you rename
# items in the code above, you must rename them here as well, and if you
# move items to another module, you must move their UUIDs with them.  In
# other words, once a UUID is assigned to a particular role, entity,
# relationship, or module, it should be kept in sync with it thereafter.
###########################################################################
\n"""

usage = """spike_uuids -- generate UUIDs for schema modules

Usage:
    RunPython -m spike_uuids [options] path/to/mod1.py [path/to/mod2.py ...]

Edits the specified Python modules to include newly-generated UUIDs for any
schema elements defined by the module that do not already have a UUID assigned
to them.

Options:
    -h, --help      Display this help message
    -v, --verbose   Display status information and generated UUIDs
    -n, --no-exec   Just display additions, don't actually alter files
"""

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


    # Quick-and-dirty argument management

    show_help = False
    no_execute = False
    verbose = False
    parse_error = None

    def parseArgs(self,argv):
        try:
            opts, self.args = getopt.getopt(
                argv[1:],'hnv','help no-exec verbose'.split()
            )
        except getopt.GetoptError:
            self.show_help = True
            self.parse_error = "%s: Invalid option(s)" % argv[0]
            self.args = []
            return

        optmap = dict(opts)
        if '--help' in optmap or '-h' in optmap:
            self.show_help = True
            return

        if '--no-exec' in optmap or '-n' in optmap:
            self.no_execute = True

        if '--verbose' in optmap or '-v' in optmap:
            self.verbose = True

        if not self.args:
            self.parse_error = "%s: no files specified" % argv[0]
            return

    def main(self,argv=None):
        if argv is None:
            argv = sys.argv
        self.parseArgs(argv)

        if self.parse_error:
            print usage
            print
            print self.parse_error
            sys.exit(2)

        elif self.show_help:
            print usage

        else:
            for arg in self.args:
                if self.verbose:
                    print "Parsing", arg
                trailer = self.fromSource(open(arg,'rt').read())
                if trailer:
                    if self.no_execute:
                        print trailer
                    else:
                        open(arg,'at').write(trailer)
                elif self.verbose:
                    print "No new UUIDs needed for",arg


def main(argv=None):
    UUIDGenerator().main(argv)


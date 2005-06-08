from application import schema
from application.Parcel import Manager as ParcelManager
from application.Parcel import Parcel
from repository.schema.Kind import Kind
from repository.persistence.RepositoryView import NullRepositoryView

import gettext, logging, os
gettext.install('chandler', 'locale')

for chatty in 'Parcel', 'Inbound':
    # Silence talkative loggers
    logger = logging.getLogger(chatty)
    logger.setLevel(logging.WARNING)

logging.getLogger().addHandler(logging.StreamHandler())

rep = NullRepositoryView()
schema.initRepository(rep)

manager = ParcelManager.get(
    rep, path=[os.path.join(os.path.dirname(__file__),'parcels')]
)

manager.loadParcels() #['http://osafoundation.org/parcels/osaf/contentmodel'])

classKinds = {}
allKinds = set()

def scan_parcel(item):
    for child in item.iterChildren():
        if isinstance(child,Parcel):
            scan_parcel(child)
        elif isinstance(child,Kind):
            classKinds.setdefault(child.getItemClass(),[]).append(child)
            allKinds.add(child)

scan_parcel(rep.findPath('//parcels'))


goodKinds = 0
unloadable = []
non_schema = []
diff_supers = []
diff_attrs = []
diff_path = []
missing = []
derived_non_schema = []
not_imported = []
all = set()
bad = set()

for cls, kinds in classKinds.items():
    classname = "%s.%s" % (
        getattr(cls,'__module__','*generated*'),cls.__name__
    )
    all.add(classname)

    if classname.startswith('repository.schema.Kind.class_'):
        missing.extend(kind.itsPath for kind in kinds)
        bad.add(classname)
        continue

    if len(kinds)>1:
        print
        print "Multiple kinds for class", classname+':'
        for kind in kinds:
            print "   ",kind.itsPath
        bad.add(classname)
        continue

    if not isinstance(cls,schema.ItemClass) and cls not in schema.nrv._schema_cache:
        if schema.Base in cls.__bases__:
            non_schema.append(classname)
        else:
            derived_non_schema.append(classname)
        continue
    try:
        item = schema.itemFor(cls)
    except:
        unloadable.append(classname)
        continue

    _hash = item.hashItem()
    attrs = set(attr.itsName for attr in item.attributes)
    supers = [sk.itsName for sk in item.superKinds]

    for kind in kinds:
        path = '.'.join(str(kind.itsPath).split('/')[3:-1])
        module = schema.importString(path)
        if cls not in module.__dict__.values():
            not_imported.append(classname)

        if kind.itsPath<>item.itsPath:
            diff_path.append(classname)
        if kind.itsName<>item.itsName:
            print
            print classname, "has a different name than", kind.itsPath

        if attrs<>set(attr.itsName for attr in getattr(kind,'attributes',())):
            diff_attrs.append(classname)
        if supers<>[sk.itsName for sk in kind.superKinds]:
            diff_supers.append(classname)



def report(title,items):
    if items:
        print
        print
        print title
        for name in sorted(items):
            print "   ",name

for title,items in [
    ("Other kinds that need a class created for them", missing),
    ("Classes that should subclass schema.Item",non_schema),
    ("Classes that inherit from classes that should subclass schema.Item",
        derived_non_schema),
    ("Classes whose schema couldn't be loaded (e.g. due to name conflicts)",
        unloadable),
    ("Classes whose path isn't correct (missing __parcel__?)",
        diff_path),
    ("Classes that aren't in the parcel module (missing import?)",
        not_imported),
    ("Classes whose superclasses don't match their parcel.xml superKinds",
        diff_supers),
    ("Classes with different or missing attributes (compared to parcel.xml)",
        diff_attrs),
]:
    bad |= set(items)
    report(title,items)

good = all - bad
report(
    "Ready to add Clouds and/or other metadata, then remove from parcel.xml",
    good
)

print
print
print len(classKinds), "classes for", len(allKinds),
print "kinds (%s good)" % len(good)


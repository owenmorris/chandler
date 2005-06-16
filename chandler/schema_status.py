from application import schema
from application.Parcel import Manager as ParcelManager
from application.Parcel import Parcel
from repository.schema.Kind import Kind
from repository.persistence.RepositoryView import NullRepositoryView
import sys, logging, os

# pre-import any command line arguments so errors can be reported sooner
report_on = [(arg, schema.importString(arg))for arg in sys.argv[1:]]
  
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
diff_clouds = []
diff_path = []
missing = []
derived_non_schema = []
all = set()
bad = set()
imports_needed = {}
details = {}

def mismatch(classname,how,what):
    details.setdefault(classname,{}).setdefault(how,[]).append(what)

def name_of(cls):
    return "%s.%s" % (
        getattr(cls,'__module__','*generated*'),cls.__name__
    )

def item_names_of(item,attr):
    return set(thing.itsName for thing in getattr(item,attr,()))
    
for cls, kinds in classKinds.items():
    classname = name_of(cls)
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

    for kind in kinds:
        modname = '.'.join(str(kind.itsPath).split('/')[3:-1])
        module = schema.importString(modname)
        if cls not in module.__dict__.values():
            imports_needed.setdefault(modname,[]).append(classname)

    if not isinstance(cls,schema.ItemClass) and cls not in schema.nrv._schema_cache:
        if schema.Base in cls.__bases__:
            non_schema.append(classname)
        else:
            for b in cls.__mro__:
                if schema.Base in b.__bases__:
                    non_schema.append(name_of(b))
            derived_non_schema.append(classname)
        continue

    try:
        item = schema.itemFor(cls)
    except:
        unloadable.append(classname)
        continue

    _hash = item.hashItem()
    attrs = item_names_of(item,'attributes')
    clouds = item_names_of(item,'clouds')
    supers = [sk.itsName for sk in item.superKinds]

    for kind in kinds:
        if kind.itsPath<>item.itsPath:
            diff_path.append(classname)
        if kind.itsName<>item.itsName:
            print
            print classname, "has a different name than", kind.itsPath

        if attrs<>item_names_of(kind,'attributes'):
            diff_attrs.append(classname)
        else:
            for attr in attrs:
                a_item = item.attributes.getByAlias(attr)
                a_kind = kind.attributes.getByAlias(attr)
                if a_item.hashItem() <> a_kind.hashItem():
                    mismatch(classname,"attributes",attr)

        if clouds<>item_names_of(kind,'clouds'):
            diff_clouds.append(classname)
        else:
            for cloud in clouds:
                e_item = item_names_of(item.clouds.getByAlias(cloud),'endpoints')
                e_kind = item_names_of(kind.clouds.getByAlias(cloud),'endpoints')
                if e_item<>e_kind:
                    mismatch(classname,"clouds",cloud)
                # else: check endpoint details against each other

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
    ("Classes whose path isn't correct (missing/wrong __parcel__?)",
        diff_path),
    ("Classes whose superclasses don't match their parcel.xml superKinds",
        diff_supers),
    ("Classes with different or missing attributes (compared to parcel.xml)",
        diff_attrs),
    ("Classes with different or missing clouds (compared to parcel.xml)",
        diff_clouds),
]:
    items = set(items)
    bad |= items
    report(title,items)

for modname,classnames in imports_needed.items():
    report("Classes that should be imported by "+modname+":", classnames)
    bad |= set(classnames)



def report_details(clsname):
    for name, items in details[clsname].items():
        report(
            "Inconsistent %s for %s:" % (name,clsname),
            items
        )
    bad.add(clsname)
    del details[clsname]
        

for name, ob in report_on:
    if ob in classKinds:
        report_details(name_of(ob))
    else:
        prefix = name+'.'
        for clsname,info in details.items():
            if clsname.startswith(prefix):
                report_details(clsname)

report(
    "Classes w/other issues (use names as arguments, to get more details):",
    details
)
bad |= set(details)

good = all - bad
report(
    "Ready to add optional metadata, then remove from parcel.xml",
    good
)

print
print
print len(classKinds), "classes for", len(allKinds),
print "kinds (%s good)" % len(good)


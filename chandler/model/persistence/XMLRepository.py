
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import cStringIO

from model.util.UUID import UUID
from model.item.Item import ItemHandler
from model.item.ItemRef import ItemRef
from model.item.ItemRef import RefDict
from model.persistence.Repository import Repository

from bsddb.db import DBEnv, DB, DB_CREATE, DB_INIT_MPOOL, DB_BTREE
from dbxml import XmlContainer, XmlDocument, XmlValue
from dbxml import XmlQueryContext, XmlUpdateContext


class DBError(ValueError):
    "All DBXML related exceptions go here"
    

class XMLRepository(Repository):
    """A Berkeley DBXML based repository.

    This simple repository implementation saves all items in separate XML
    item files in a given directory. It can then load them back to restore
    the same exact item hierarchy."""

    def __init__(self, dbHome):
        'Construct an XMLRepository giving it a DBXML container pathname'
        
        super(XMLRepository, self).__init__()

        self.dbHome = dbHome
        self._env = None
        self._ctx = XmlQueryContext()
        
    def create(self):

        if self._env is None:
            super(XMLRepository, self).create()
            self._env = DBEnv()
            self._env.open(self.dbHome, DB_CREATE | DB_INIT_MPOOL, 0)
            self._refs = XMLRepository.refContainer(self._env, "__refs__")
            self._schema = XMLRepository.xmlContainer(self._env, "__schema__")
            self._data = XMLRepository.xmlContainer(self._env, "__data__")

    def open(self, verbose=False):

        if self._env is None:
            self.create()
            self._load(verbose=verbose)

    def close(self, purge=False, verbose=False):

        if self._env is not None:
            self._save(purge=purge, verbose=verbose)
            self._refs.close()
            self._data.close()
            self._schema.close()
            self._env.close()
            self._env = None

    def isOpen(self):

        return self._env is not None

    def _load(self, verbose=False):

        if not self.isOpen():
            raise DBError, "Repository is not open"

        def load(container):

            hooks = []

            for value in container.query("/item"):
                self._loadItemString(value.asDocument().getContent(),
                                     verbose=verbose, afterLoadHooks=hooks)

            self.resolveOrphans()
            for hook in hooks:
                hook()

        load(self._schema)
        load(self._data)

    def purge(self):

        def purge(container):

            for value in container.query("/item"):
                doc = value.asDocument()
                for u in doc.queryWithXPath("/item/@uuid"):
                    uuid = UUID(u.asString())
                    if not self._registry.has_key(uuid):
                        container.deleteDocument(doc)

        purge(self._schema)
        purge(self._data)

    def _save(self, purge=False, verbose=False):

        if not self.isOpen():
            raise DBError, "Repository is not open"

        if purge:
            self.purge()

        hasSchema = self._roots.has_key('Schema')

        if hasSchema:
            self._saveRoot(self.getRoot('Schema'), self._schema,
                           True, verbose)
        
        for root in self._roots.itervalues():
            name = root.getName()
            if name != 'Schema':
                self._saveRoot(root, self._data,
                               not hasSchema, verbose)

    def _saveRoot(self, root, container,
                  withSchema=False, verbose=False):

        root.save(self, container = container,
                  withSchema = withSchema, verbose = verbose)

    def saveItem(self, item, **args):

        if args.get('verbose'):
            print item.getPath()
            
        container = args['container']
        for oldDoc in container.find(item.getUUID()):
            container.deleteDocument(oldDoc)

        out = cStringIO.StringIO()
        generator = xml.sax.saxutils.XMLGenerator(out, 'utf-8')
        generator.startDocument()
        item.toXML(generator, args.get('withSchema', False))
        generator.endDocument()

        doc = XmlDocument()
        doc.setContent(out.getvalue())
        out.close()

        container.putDocument(doc)

    def createRefDict(self, item, name, otherName, ordered=False):

        return XMLRefDict(self, item, name, otherName, ordered)


    class xmlContainer(object):

        def __init__(self, env, name):

            super(XMLRepository.xmlContainer, self).__init__()
        
            self._xml = XmlContainer(env, name)
            if not self._xml.exists(None):
                self._xml.open(None, DB_CREATE)
                self._xml.addIndex(None, "", "item",
                                   "edge-attribute-equality-string")
            else:
                self._xml.open(None, 0)

            self._ctx = XmlQueryContext()
            self._ctx.setReturnType(XmlQueryContext.ResultDocuments)
            self._ctx.setEvaluationType(XmlQueryContext.Lazy)
            self._updateCtx = XmlUpdateContext(self._xml)

        def find(self, uuid):

            self._ctx.setVariableValue("uuid", XmlValue(uuid.str64()))
            for value in self._xml.queryWithXPath(None, "/item[@uuid=$uuid]",
                                                  self._ctx):
                yield value.asDocument()

        def query(self, xpath, context=None):

            return self._xml.queryWithXPath(None, xpath, context)

        def deleteDocument(self, doc):

            self._xml.deleteDocument(None, doc, self._updateCtx)

        def putDocument(self, doc):

            self._xml.putDocument(None, doc, self._updateCtx)

        def close(self):

            self._xml.close()
            self._xml = None


    class refContainer(object):

        def __init__(self, env, name):

            super(XMLRepository.refContainer, self).__init__()
        
            self._db = DB(env)
            self._db.open(name, None, DB_BTREE, DB_CREATE)
            
        def close(self):

            self._db.close()
            self._db = None

        def put(self, key, value):

            self._db.put(key, value);

        def get(self, key):

            return self._db.get(key);


class XMLRefDict(RefDict):

    def __init__(self, repository, item, name, otherName, ordered)
        
        super(XMLRefDict, self).__init__(item, name, otherName, ordered)

        self._repository = repository
        self._buffer = cStringIO.StringIO()

    def __setitem__(self, key, value):

        if self._item is not None:
            other = value.other(self._item)

            if other is not None:
                self._writeRef(other)

       super(RefDict, self).__setitem__(key, value)

    def _writeRef(self, item):

        self._buffer.seek(31, 0)

        if isinstance(key, UUID):
            self._buffer.write(key._uuid)
        else:
            self._buffer.write(key)

        self._repository._refs.put(self._buffer.getvalue(), other._uuid._uuid)

    def __getitem__(self, key):

#        value = super(dict, self).get(key, None)
#        if value is not None:
#            return value
#
#        self._buffer.reset()
#        self._buffer.write(item._uuid._uuid)
#        self._buffer.write(uuid._uuid)
#
#        if isinstance(key, UUID):
#            self._buffer.write(key._uuid)
#        else:
#            self._buffer.write(key)
#
#        uuid = UUID(self._repository._refs.get(self._buffer.getvalue()))
#        other = self.repository.find(uuid)

        return super(RefDict, self).__getitem__(key)
        
    def _setItem(self, item):

        if self._item is not None and self._item is not item:
            raise ValueError, 'Item is already set'
        
        self._item = item

        if item is not None:
            if item._kind is not None:
                attrDef = item._kind.getAttrDef(name)
                if attrDef is not None:
                    uuid = attrDef.getUUID()
                else:
                    uuid = UUID()
            else:
                uuid = UUID()

            self._buffer.reset()
            self._buffer.write(self._item._uuid._uuid)
            self._buffer.write(uuid._uuid)

            for item in self:
                self._writeRef(item)
            

    def _xmlValues(self, generator):

        for ref in self._iteritems():
            ref[1]._xmlValue(ref[0], self._item, generator)

#        generator.startElement('db', {})
#        generator.characters(self._uuid.str64())
#        generator.endElement('db')


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

from bsddb.db import DBEnv, DB, DB_CREATE, DB_TRUNCATE, DB_INIT_MPOOL, DB_BTREE
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
        self._transaction = {}
        
    def create(self):

        if self._env is None:
            super(XMLRepository, self).create()
            self._env = DBEnv()
            self._env.open(self.dbHome, DB_INIT_MPOOL, 0)
            self._refs = XMLRepository.refContainer(self._env, "__refs__",
                                                    True)
            self._schema = XMLRepository.xmlContainer(self._env, "__schema__",
                                                      True)
            self._data = XMLRepository.xmlContainer(self._env, "__data__",
                                                    True)

    def open(self, verbose=False):

        if self._env is None:
            super(XMLRepository, self).open()
            self._env = DBEnv()
            self._env.open(self.dbHome, DB_INIT_MPOOL, 0)
            self._refs = XMLRepository.refContainer(self._env, "__refs__")
            self._schema = XMLRepository.xmlContainer(self._env, "__schema__")
            self._data = XMLRepository.xmlContainer(self._env, "__data__")
            self._load(verbose=verbose)

    def close(self, purge=False, verbose=False):

        if self._env is not None:
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
                                     verbose=verbose, afterLoadHooks=hooks,
                                     loading=True)

            self.resolveOrphans()
            for hook in hooks:
                hook()

        load(self._schema)
        load(self._data)

    def purge(self):
        pass

    def save(self, purge=False, verbose=False):

        if not self.isOpen():
            raise DBError, "Repository is not open"

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

        log = self._transaction.get(root.getName(), None)
        if log is not None:
            for item in log:
                self.saveItem(item, container = container,
                              withSchema = withSchema, verbose = verbose)
            del log[:]

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

    def addTransaction(self, item):

        if not self.isOpen():
            raise DBError, 'Repository is not open'

        name = item.getRoot().getName()
        if self._transaction.has_key(name):
            self._transaction[name].append(item)
        else:
            self._transaction[name] = [ item ]
    

    class xmlContainer(object):

        def __init__(self, env, name, create=False):

            super(XMLRepository.xmlContainer, self).__init__()
        
            self._xml = XmlContainer(env, name)

            if create:
                if self._xml.exists(None):
                    self._xml.remove(None)

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

        def __init__(self, env, name, create=False):

            super(XMLRepository.refContainer, self).__init__()
        
            self._db = DB(env)

            if create:
                self._db.open(name, None, DB_BTREE, DB_CREATE | DB_TRUNCATE)
            else:
                self._db.open(name, None, DB_BTREE)
            
        def close(self):

            self._db.close()
            self._db = None

        def put(self, key, value):

            self._db.put(key, value)

        def delete(self, key, value):

            self._db.delete(key, value)

        def get(self, key):

            return self._db.get(key)

        def cursor(self):

            return self._db.cursor()


class XMLRefDict(RefDict):

    def __init__(self, repository, item, name, otherName, ordered):
        
        self._log = []
        self._item = None
        self._uuid = UUID()
        self._buffer = cStringIO.StringIO()
        self._repository = repository

        super(XMLRefDict, self).__init__(item, name, otherName, ordered)

    def _detach(self, itemRef, item, name, other, otherName):

        if other is not None:
            self._log.append((1, other.refName(name), other.getUUID()))

    def _attach(self, itemRef, item, name, other, otherName):

        if other is not None:
            self._log.append((0, other.refName(name), other.getUUID()))
        
    def _writeRef(self, key, uuid):

        self._buffer.truncate(32)
        self._buffer.seek(0, 2)

        if isinstance(key, UUID):
            self._buffer.write('\0')
            self._buffer.write(key._uuid)
        else:
            self._buffer.write('\1')
            self._buffer.write(key)

        self._repository._refs.put(self._buffer.getvalue(), uuid._uuid)

    def _eraseRef(self, key, uuid):

        self._buffer.truncate(32)
        self._buffer.seek(0, 2)

        if isinstance(key, UUID):
            self._buffer.write('\0')
            self._buffer.write(key._uuid)
        else:
            self._buffer.write('\1')
            self._buffer.write(key)

        self._repository._refs.delete(self._buffer.getvalue(), uuid._uuid)

    def _dbRefs(self):

        self._buffer.truncate(32)
        key = self._buffer.getvalue()

        cursor = self._repository._refs.cursor()

        val = cursor.set_range(key)
        while val is not None and val[0].startswith(key):
            if val[0][32] == '\0':
                k = UUID(val[0][33:])
            else:
                k = val[0][33:]

            yield (k, UUID(val[1]))
            val = cursor.next()

        cursor.close()

    def _setItem(self, item):

        if self._item is not None and self._item is not item:
            raise ValueError, 'Item is already set'
        
        self._item = item
        if item is not None:
            self._prepareKey(item._uuid, self._uuid)

    def _prepareKey(self, uItem, uuid):

        self._uuid = uuid

        self._buffer.reset()
        self._buffer.write(uItem._uuid)
        self._buffer.write(uuid._uuid)
            
    def _xmlValues(self, generator):

        for entry in self._log:
            if entry[0] == 0:
                self._writeRef(entry[1], entry[2])
            else:
                self._eraseRef(entry[1], entry[2])
        del self._log[:]

        if len(self) > 0:
            generator.startElement('db', {})
            generator.characters(self._uuid.str64())
            generator.endElement('db')

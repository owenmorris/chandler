
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import xml.sax, xml.sax.saxutils
import cStringIO

from model.util.UUID import UUID
from model.item.Item import ItemHandler
from model.persistence.Repository import Repository

from bsddb3.db import DBEnv, DB_CREATE, DB_INIT_MPOOL
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
        
    def open(self):

        if self._env is None:
            self._env = DBEnv()
            self._env.open(self.dbHome, DB_CREATE | DB_INIT_MPOOL, 0)
            self._schema = XMLRepository.xmlContainer(self._env, "__schema__")
            self._data = XMLRepository.xmlContainer(self._env, "__data__")

    def close(self):

        if self._env is not None:
            self._data.close()
            self._schema.close()
            self._env.close()
            self._env = None

    def isOpen(self):

        return self._env is not None

    def load(self, verbose=False):

        if not self.isOpen():
            raise DBError, "Repository is not open"

        def load(container):

            cover = Repository.stub(self)
            hooks = []

            for value in container.query("/item"):
                self._loadItemString(value.asDocument().getContent(), cover,
                                     verbose=verbose, afterLoadHooks=hooks)
            for item in cover:
                if item.__dict__.has_key('_parentRef'):
                    item.move(self.find(item._parentRef))
                    del item._parentRef

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

    def save(self, encoding='iso-8859-1', purge=False, verbose=False):

        if not self.isOpen():
            raise DBError, "Repository is not open"

        if purge:
            self.purge()

        hasSchema = self._roots.has_key('Schema')

        if hasSchema:
            self._saveRoot(self.getRoot('Schema'), self._schema,
                           encoding, True, verbose)
        
        for root in self._roots.itervalues():
            name = root.getName()
            if name != 'Schema':
                self._saveRoot(root, self._data,
                               encoding, not hasSchema, verbose)

    def _saveRoot(self, root, container, encoding='iso-8859-1',
                  withSchema=False, verbose=False):

        root.save(self, container = container,
                  encoding = encoding, withSchema = withSchema,
                  verbose = verbose)

    def saveItem(self, item, **args):

        if args.get('verbose'):
            print item.getPath()
            
        container = args['container']
        for oldDoc in container.find(item.getUUID()):
            container.deleteDocument(oldDoc)

        out = cStringIO.StringIO()
        generator = xml.sax.saxutils.XMLGenerator(out, args.get('encoding',
                                                                'iso-8859-1'))
        generator.startDocument()
        item.toXML(generator, args.get('withSchema', False))
        generator.endDocument()

        doc = XmlDocument()
        doc.setContent(out.getvalue())
        out.close()

        container.putDocument(doc)


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

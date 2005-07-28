
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004, 2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import QueryParser
import repository.item.Item as Item
import sets
from datetime import date, datetime
from chandlerdb.util.uuid import UUID
import repository.item.Monitors as Monitors

import logging
log = logging.getLogger("repository.query")
log.setLevel(logging.INFO)

import time


class Query(Item.Item):

    def __init__(self, name = None, parent=None, kind=None, queryString = "", *values, **kwds):
        """
        @param repo: The repository associated with the query @@@ replace with factory method
        @type repo: Repository
        
        @param queryString: A string containing the query to be processed
        @type queryString: string
        """
        log.debug(u"RepoQuery.__init__: ")

        super(Query, self).__init__(name, parent, kind, *values, **kwds)

        self._queryString = queryString
        self._logical_plan = None
        self.__init()
        
    def __init(self):
        """
        __init is a private constructor method 
        (following the convention in the rest of the repository)
        """
        # these attributes need to be setup after we reload
        self._otherViewSubscribeCallbacks = {}
        self._sameViewSubscribeCallbacks = {}
        self._sameViewNames = [] # names of view that we are monitoring on
        self._removedSinceCommit = []
        self._queryStringIsStale = True

    def _fillItem(self, name, parent, kind, **kwds):
        """
        Fill in the python attributes
        """
        # We're using _fillItem in lieu of onItemLoad and onItemCopy because there is
        # a window during item loading where self.__init() will not get called until
        # it is too late.
        
        # you must call super when using _fillItem
        super(Query, self)._fillItem(name, parent, kind, **kwds)
        self.__init()

    def getQueryString(self):
        return self._queryString

    def setQueryString(self, queryString):
        if queryString == self._queryString: 
            return
        self._queryString = queryString
        self._queryStringIsStale = True

    def getArgs (self):
        return self._args

    def setArgs (self, value):
        if self._args == value:
            return
        self._args = value
        self.stale = True

    args = property (getArgs, setArgs)

    queryString = property(getQueryString, setQueryString)

    def _compile(self):
        """
        Compile this query

        Before calling compile, be sure that they queryString
        and any parameters have been set
        """
        if not self.queryString or self.queryString == "":
            return

        log.debug(u"RepoQuery.compile(): %s" % self.queryString)

        if self.queryString:
            self.ast = QueryParser.parse('stmt', self.queryString)
            log.debug(u"compile: AST = %s" % self.ast)
            self._logical_plan = self.__analyze(self.ast)
            self._queryStringIsStale = False
            self.stale = True
        else:
            self._logical_plan = None
            self.stale = True

    def subscribe(self, callbackItem = None, callbackMethodName = None, inSameView = True, inOtherViews = True):
        """
        This query should subscribe to repository changes

        @param callbackItem: a Chandler Item that provides a callback method
        @type callbackItem: Item

        @param callbackMethodName: The name of the callback method on the callbackItem
        @type callbackMethodName: string

        @param inSameView: if we should subscribe to changes in the current view
        @type inSameView: Boolean
        @param inOtherViews: if we should subscribe to changes from commits in other views
        @type inOtherViews: Boolean
        """
        if callbackItem is not None:
            if inSameView:
                self._sameViewSubscribeCallbacks [callbackItem.itsUUID] = callbackMethodName
                self._sameViewNames.append(self.itsView.name)
            if inOtherViews:
                self._otherViewSubscribeCallbacks[callbackItem.itsUUID] = callbackMethodName
                #@@@ add monitor for items in result set
        if inOtherViews:
            log.debug(u"RepoQuery<>.subscribe(): %s" % (self.queryString))
            self.itsView.addNotificationCallback(self.queryCallback)        
            
        try:
            self._compile()
        except AttributeError:
            print "compile failed", ae
        
    def unsubscribe(self, callbackItem=None, inSameView = True, inOtherViews = True):
        """
        This query should stop subscribing to repository changes. If you don't specify a
        callbackItemUUID, all subscriptions will be removed.

        @param callbackItem: callbackItem to be removed
        @type callbackItem: Item
        @param inSameView: if we should remove the item from the view subscriptions
        @type inSameView: Boolean
        @param inOtherViews: if we should remove the item from the commit subscriptions
        @type inOtherViews: Boolean
        """
        if callbackItem is None:
            if inOtherViews:
                self._otherViewSubscribeCallbacks = {}
            if inSameView:
                self._sameViewSubscribeCallbacks = {}
                self._sameViewNames = []
        else:
            if inOtherViews:
                #@@@ hack to solve KeyError on multiple blocks unsubscribing
                #from same itemcollection. -brendano
                if callbackItem.itsUUID in self._otherViewSubscribeCallbacks:
                    del self._otherViewSubscribeCallbacks [callbackItem.itsUUID]
            if inSameView:
                #@@@ hack again -brendano
                if callbackItem.itsUUID in self._sameViewSubscribeCallbacks:
                    del self._sameViewSubscribeCallbacks [callbackItem.itsUUID]
                    
                self._sameViewNames.remove(self.itsView.name)
                #@@@ remove monitor for items in result set
        
        if inOtherViews:        
            self.itsView.removeNotificationCallback(self.queryCallback)
        return len (self._otherViewSubscribeCallbacks)

    def _ensureQueryIsCurrent(self):
        """
        This routine makes sure that the compiled version of the
        query is consistent with the actual query string
        
        It is necessary because of the use of lazy evaluation in
        the implementation
        
        Call this method on code paths which will require access
        to the _logical_plan (e.g. generating query results, or 
        processing incremental changes"
        """
        if self._queryStringIsStale and self.queryString:
            self._compile()

    def queryCallback(self, view, changes, notification, **kwds):
        """
        queryCallback implements the callback used by L{Repository.addNotificationCallback<repository.persistence.Repository.Repository.addNotificationCallback>}

        It is responsible for determining whether committed items
        enter or exit the result set of a particular query
        
        @param changes: a list of changes received from the repository notification mechanism
        @type changes: list
    
        @param notification: a string containing the kind of notification
        @type notification: string
        """
        if self.itsView != view:
            return
        start = time.time()
        log.debug(u"RepoQuery.queryCallback for %s" % self.queryString)

        # we can commit before we've compiled the query
        #@@@ This should be an error, I think
        self._ensureQueryIsCurrent()
        if not self.queryString:
            return
        changed = False

        #@@@ change this to batch notifications
        added = []
        removed = []
        changed_uuids = []
        for uuid, reason, kwds in changes:
            i = None # kill this
            i = view.findUUID(uuid)
           #@@@ there's a big problem with this if there are paths through multiple items -- we're going to need something fairly sophisticated here.
            if i is not None:
                log.debug(u"RepoQuery.queryCallback %s:%s" % (i, i.itsKind))
                flag = self._logical_plan.changed(i)
                if flag is not None:
                    changed = True
                    if flag:
                        self._resultSet.append(i)
                        added.append(i.itsUUID)
                    else:
                        if i in self._resultSet: # should we need this?
                            self._resultSet.remove(i)
                            removed.append(i.itsUUID)
                        elif i in self._removedSinceCommit:
                            removed.append(i.itsUUID)
            elif notification == 'changeonly':
                if i is not None and i.itsUUID in self._resultSet:
                    changed = True
                    changed_uuids.append(i.itsUUID)
                
        self._removedSinceCommit = [] # reset for next commit

        if changed:
            log.debug(u"RepoQuery.queryCallback: %s %s query result" % (uuid, [added, removed, changed_uuids] ))
            for callbackUUID in self._otherViewSubscribeCallbacks:
                item = view.find (callbackUUID)
                """
                  We allow subscriptions to items without callbacks. This used to keep the _resultSet up to date
                when notifications aren't required -- DJA
                """
                methodName = self._otherViewSubscribeCallbacks [callbackUUID]
                if methodName:
                    method = getattr (type(item), methodName)
                    method (item, (added,removed))
        log.debug(u"queryCallback: %s:%f" % (self.queryString, time.time()-start))

    def __len__ (self):
        return len (self.resultSet)

    def __contains__ (self, item):
        return item in self.resultSet

    def __iter__(self):
        """
        Return a generator of the query results
        """
        if self.__resultsAreStale():
            if self._resultSet:
                self._resultSet.clear()
            if self.stale:
                self.stale = False
            for i in self._logical_plan.execute():
                self._resultSet.append(i)
                yield i
        else: 
            for i in self._resultSet:
                yield i

    def getResultSet(self):
        """
        Return a reference collection of the query results
        """
        if self.__resultsAreStale():
            if self._resultSet:
                self._resultSet.clear()
            if self.stale:
                self.stale = False
            for i in self._logical_plan.execute():
                self._resultSet.append(i)
            return self._resultSet
        else: 
            return self._resultSet

    resultSet = property(getResultSet)

    def __resultsAreStale(self):
        self._ensureQueryIsCurrent()
        if self.queryString == "":
            if self._resultSet:
                self._resultSet.clear()
            if self.stale:
                self.stale = False
        return self.stale

    def __analyze(self, ast):
        """
        Produce a logical level query plan for the AST
        
        @param ast: A list (tree) containg the AST tree
        @type ast: list
        """                   
        log.debug(u"__analyze %s" % ast)
        queryType = ast[0]
        queryArgs = ast[1:]

        if queryType == 'for':
            plan = ForPlan(self, queryArgs, self._args)
        elif queryType == 'union':
            childPlans = [ self.__analyze(i) for i in queryArgs[0] ]
            plan = UnionPlan(self, childPlans)
        elif queryType == 'intersect':
            childPlans = [ self.__analyze(i) for i in queryArgs[0:2] ]
            plan = IntersectionPlan(self, childPlans)
        elif queryType == 'difference':
            childPlans = [ self.__analyze(i) for i in queryArgs[0:2] ]
            plan = DifferencePlan(self, childPlans)
        else:
            raise ValueError, "Unrecognized operator %s" % op

        return plan

    def monitorCallback(self, op, item, attribute, *args, **kwds):
        #@@@ the following try block is an attempt to generate useful output to help track down 2535 - it will be removed when we fix the bug
        if not self.itsView.name in self._sameViewNames:
            return

        self._ensureQueryIsCurrent()
        flag = self._logical_plan.monitored(op, item, attribute, *args, **kwds)
        if flag is not None:
            if flag:
                action = ([item], [])
                self._resultSet.append(item)
            else:
                action = ([], [item])
                if item in self._resultSet:
                    self._resultSet.remove(item)
                    self._removedSinceCommit.append(item)
            
            for callbackUUID in self._sameViewSubscribeCallbacks:
                i = self.itsView.find(callbackUUID)
                """
                  We allow subscriptions to items without callbacks. This used to keep the _resultSet up to date
                when notifications aren't required -- DJA
                """
                methodName = self._sameViewSubscribeCallbacks[callbackUUID]
                if methodName:
                    method = getattr(type(i), methodName)
                    method(i, action)

class LogicalPlan(object):
    """
    Abstract (interface, really) class for Logical Plan
    """
    def __init__(self, ast):
        pass

class ForPlan(LogicalPlan):
    """
    Logical plan which implements for queries
    """
    def __init__(self, item, ast, args):
        """
        constructor

        @param item: the query item for this plan
        @type item: Item

        @param ast: an abstract syntax tree of the query
        @type ast: list

        @param args: the set of query parameters/arguments
        @type arts: dict
        """
        self.__item = item # need an item for Monitors.attach
        assert self.__item is not None, "For plan's query item not set"
        self._args = args #@@@ AUAUGUGUGH
        self._pathKinds = {}
        self.affectedAttributes = [] # attributes that we need to watch
        self.analyze(ast)

    def lookup_source(self, name):
        """
        Convert a query source to a collection

        @param name: the source specified in the query
        @type name: a string (kind path or argument) or a tuple (ftcontains, lucene query)
        """
        # ftcontains
        if type(name) == tuple and name[0] == 'ftcontains':
            return name

        # "/path/to/kind"
        #@@ don't enclose kind paths in ""?
        if (name.startswith('"') and name.endswith('"')) or \
           (name.startswith("'") and name.endswith("'")):
            name = name[1:-1]
        kind = self.__item.itsView.findPath(name)
        if kind is not None:
            return ('kind', kind)

        # $argument
        if name.startswith('$'): 
            itemUUID, attribute = self._args[name]
            if isinstance (itemUUID, UUID):
                return ('argsrc', itemUUID, attribute)
            else:
                if attribute is None:
                    return('arg', itemUUID)
                else:
                    return ('arg',item.getAttr(attribute))
        assert False, "lookup_source couldn't handle %s" % name

    def compile_predicate(self, ast):
        """
        Compile an abstract syntax tree into a python expression
        that can be passed to eval

        @param ast:
        @type ast: list (tree)
        """

        # These lists control the functions and operators allowed
        # in query predicate expressions
        infix_ops = ['+','-','*','/','div','mod','==','!=','>=','<=','>','<','and','or']
        infix_fns = ['contains']
        binary_fns = []
        unary_ops = ['not']
        unary_fns = ['date','len']

        def infix_op(op, args):
            """
            Helper function to construct an infix operator
            """
            log.debug(u"infix op: %s %s" % (op, args))
            return "%s %s %s" % (self.compile_predicate(args[0]), op, self.compile_predicate(args[1]))

        log.debug(u"compile_predicate: ast=%s, ast[0]=%s" % (ast,ast[0]))
        # function
        token = ast[0]
        if token == 'fn':
            fn = ast[1]
            args = ast [2:][0]
            log.debug(u"%s %s %s" % (token, fn, args))
            if fn in unary_fns and len(args) == 1:
                if fn == 'date':
                    pred = "datetime(*map(int, %s.split('-')))" % self.compile_predicate(args[0])
                else:
                    pred = "%s(%s)" % (fn, self.compile_predicate(args[0]))
            elif fn in binary_fns and len(args) == 2: 
                pred = fn+'('+self.compile_predicate(args[0])+','+self.compile_predicate(args[1])+')'
            elif fn in infix_fns:
                if fn == 'contains':
                    pred = infix_op('in', [args[1],args[0]])
                else:
                    pred = infix_op(fn, [args[0], args[1]])
            else:
                assert False, "unhandled fn %s" % fn
            return pred
        # unary operators
        elif token in unary_ops and len(ast[1:]) == 1:
            pred = "%s %s" % (ast[0], self.compile_predicate(ast[1]))
            return pred
        # infix operators
        elif token in infix_ops:
            args = ast[1:]
            return infix_op(ast[0],[args[0],args[1]])
        # path expression
        elif token is 'path': 
            # handle path expressions by computing the set of kinds/types covered
            # by the attributes along a path.  changed() will check commit against
            # this list of types to do incremental checking of multi-item paths

            #@@@ do iteration variable checks
            source = self.lookup_source(self.iter_source)
            path_type = source[0]
            args = ast[1]

            if path_type == 'kind':
                current = source[1]
                count = 1
                # walk path, building reverse lookup to be used by changed()
                for i in args[1:]:
                    try:
                        if (i.startswith('its')):
                            attr = getattr(current, i)
                        else:
                            attr = current.getAttribute(i)
                    except AttributeError:
                        #@@@ raise a compilation error?
                        #@@@What about the case where only some items only have the attr?
                        break

                    # stop at literal attributes
                    if type(attr) == str or type(attr) == unicode:
                        break
                    if attr.hasLocalAttributeValue('otherName'):
                        if attr.hasLocalAttributeValue(attr.otherName):
                            #@@@ need to handle list cardinality!
                            current = attr.getAttributeValue(attr.otherName).first()
                        else:
                            current = current.getAttribute(i).type
                        #@@@ this needs to generalize to multiple path expressions per predicate
                        self._pathKinds[current] = (attr.otherName, count)
            self.affectedAttributes.append(args[1])
            return '.'.join(args)
        # other methods
        elif token is 'method':
            path = ast[1]
            args = ast[2]
            #@@@ check method name against approved list
            methodName = path[1][1]
            if methodName == 'hasLocalAttributeValue':
                self.affectedAttributes.append(args[0][1:-1]) # strip quotes
            return  '.'.join(path[1])+"("+','.join(args)+")"
        # string constant or iteration variable or parameter ($1)
        elif type(ast) == str or type(ast) == unicode: 
            #@@@ check that ast != iteration variable, or parameter
            if ast.startswith('$'):
                key = ast
                arg = self._args[key][0]
                if arg.isdigit():
                    return arg
                else:
                    return '"'+arg+'"'
                #@@@ any other values for $params?
            else:
                return ast
        assert False, "unhandled predicate: operator=%s, args=%s, type(args)=%s" % (op, ast, type(ast))

    def analyze(self, ast):
        """
        Produce a logical plan (collection name, compiled predicate) that
        corresponds to the 'for' statement represented by the AST.
        (The AST is actually the arguments to 'for')
        
        @param ast: the abstract syntax tree for a query
        @type ast: list
        """
        log.debug(u"analyze_for: %s" % ast)
        
        self.iter_var = ast[0]
        self.iter_source = ast[1]

        # this next line is for when we do notification checks ahead of query exexecution, as when we re-read a stored result set.
        self._sourceKind = self.lookup_source(self.iter_source)[1] 
        predicate = ast[2]
        self.recursive = ast[3]
        
        log.debug(u"analyze_for: var = %s, source = %s, predicate = %s" % (self.iter_var, self.iter_source, predicate))
        
        self.collection = self.lookup_source(self.iter_source)
        self.closure = self.compile_predicate(predicate) #@@@ duplicate
        self._predicate = self.closure
        
        log.debug(u"analyze_for: collection = %s, closure = %s" % (self.collection, self.closure))
            
        self.plan = (self.collection, compile(self.closure,'<string>','eval'))
        if len(self.__item._sameViewSubscribeCallbacks) > 0:
            Monitors.Monitors.attach(self.__item, 'monitorCallback', 'schema', 'kind')
            for a in self.affectedAttributes:
                Monitors.Monitors.attach(self.__item, 'monitorCallback', 'set', a)

    def execute(self):
        """
        Execute the query plan for a for statement
        """
        source = self.plan[0]
        sourceType = source[0]

        # source is full text
        if type(source) == tuple and sourceType == 'ftcontains': 
            args = source[1]
            textItems = self.__item.itsView.searchItems(args[0])
            items = []
            for i in textItems:
                s = i[1]
                if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
                    s = s[1:-1]
                if s in args[1:]:
                        items.append(i[0])
                else:
                    items.append(i[0])
        # source is a Kind
        elif sourceType == 'kind':
            self._sourceKind = source[1]
            self._predicate = self.plan[1]

            import repository.item.Query as RepositoryQuery
            items = RepositoryQuery.KindQuery(recursive=self.recursive).run([self._sourceKind])
        # source is an argument (ref-collection)
        elif sourceType == 'argsrc':
            items = self._getSourceIterator(source)
        elif sourceType == 'arg':
            items = source[1]
        else:
            assert False, "ForPlan.execute couldn't handle %s " % str(source)

        for i in items:
            try:
                c = eval(self._predicate)
                if c:
#                    if len(self.__item._sameViewSubscribeCallbacks) > 0:
#                        if  len(self.affectedAttributes) > 1:
#                            print "monitoring of multi-item paths is not yet supported"
                    yield i
            except AttributeError, ae:
                log.debug(u"AttributeError, %s" % ae)
                pass

    def _getSourceIterator(self, source):
        if len(source) == 3:
            arg, uuid, attrName = source
        else:
            arg, uuid = source
            attrName = None
        item = self.__item.itsView.findUUID(uuid)
        if attrName:
            items = item.getAttributeValue(attrName)
        else:
            items = item
        return items

    def monitored(self, op, item, attribute, *args, **kwds):
        return self.changed(item, attribute, op)

    def changed(self, item, attribute=None, monitorOp=None):
        """
        determine whether item has entered/exited the query result set

        @param item: an item that has been changed by commit
        @type item:

        @param attribute: the attribute on the item that was modified
        @type attribute:
            
        @param monitorOp: the name of the monitor op type, if changed was called via a monitor
        @type string:

        @rtype: boolean
        @return: true if the item entered, false if it exited, None if it was unaffected
        """
        # query source is a ref collection
        if self.collection[0] == 'argsrc':
            items = self._getSourceIterator(self.collection)
            if item in items:
                i = item
                result = eval(self._predicate)
            else:
                result = None
            return result
        #@@@ query source is a lucene query
        
        # query source is a Kind
        i = item #@@@ predicates are hardwired to 'i'

        # is the item's kind in the set covered by the predicate?
        if i.itsKind in self._pathKinds:
            # the item may be in the middle of a path expression
            # so try to walk backwards until we reach the kind that is the root of the query
            kind, count = self._pathKinds[i.itsKind]
            right_i = i
            for x in range(count):
                right_i = right_i.getAttributeValue(self._pathKinds[right_i.itsKind][0])
            i = right_i

#        try: # in case someone commits before the query is ever compiled
            # handle recursive queries
        if self.recursive:
            rightKind = i.isItemOf(self._sourceKind)
        else:
            rightKind = i.itsKind is self._sourceKind

        if rightKind:
            if monitorOp == 'kind': # monitorOp only exists when called from a monitor
                result = True
            else:
                result = eval(self._predicate)
                log.debug(u"change(): %s %s %s" % (i, self._predicate, result))
        else:
            result = None

        #log.debug(u"changed: %s, %s" % (i, result))
        return result

class UnionPlan(LogicalPlan):
    """
    Logical plan which implements for queries
    """

    def __init__(self, item, ast):
        """
        constructor

        @param rep: a repository instance
        @type rep: Repository

        @param ast: an abstract syntax tree of the query
        @type ast: list
        """
        self.__item = item
        self.analyze(ast)

    def analyze(self, plans):
        """
        Produce a logical plan that corresponds to the 'union' statement
        represented by the AST.
        (The AST is actually the list of arguments to 'union')

        @param plans: a list of Logical Plans, one per arm of the union statement
        @type plans: list
        """
        self.__plans = plans

    def execute(self):
        """
        Execute the query plan for a union statement
        """
        plans = self.__plans
        log.debug(u"__execute_union: plan = %s" % plans)
        
        s = sets.Set(plans[0].execute())
        for p in plans[1:]:
            s1 = sets.Set(p.execute())
            s.union_update(s1)
        return s
        
    def changed(self, item, attribute=None, monitorOp=None):
        """
        determine whether item has entered/exited the query result set

        @param item: an item that has been changed by commit
        @type item:

        @param attribute: the attribute on the item that was modified
        @type attribute:

        @param monitorOp: the name of the monitor op type, if changed was called via a monitor
        @type string:

        @rtype: boolean
        @return: true if the item entered, false if it exited, None if it was unaffected
        """
        bools = [ x.changed(item, attribute) for x in self.__plans ]
        bools = [ x for x in bools if x is not None ]
        if bools != []:
            return reduce((lambda x,y: x or y), bools)
        return None

    def monitored(self, op, item, attribute, *args, **kwds):
        return self.changed(item, attribute, op)
    
class IntersectionPlan(LogicalPlan):
    """
    Logical plan which implements for queries
    """
    def __init__(self, item, ast):
        """
        constructor

        @param rep: a repository instance
        @type rep: Repository

        @param ast: an abstract syntax tree of the query
        @type ast: list
        """
        self.__item = item
        self.analyze(ast)

    def analyze(self, plans):
        """
        Produce a logical plan that corresponds to the 'intersect' statement
        represented by the AST.
        (The AST is actually the list of arguments to 'intersect')

        @param plans: a list of Logical Plans, one per arm of the intersect statement
        @type plans: list
        """
        self.__plans = plans

    def execute(self):
        """
        Execute the query plan for an intersect statement
        """
        plans = self.__plans
        log.debug(u"__execute_intersect: plan = %s" % plans)
        s1 = sets.Set(plans[0].execute())
        s2 = sets.Set(plans[1].execute())
        return s1.intersection(s2)

    def changed(self, item, attribute=None, monitorOp=None):
        """
        determine whether item has entered/exited the query result set

        @param item: an item that has been changed by commit
        @type item:

        @param attribute: the attribute on the item that was modified
        @type attribute:

        @param monitorOp: the name of the monitor op type, if changed was called via a monitor
        @type string:

        @rtype: boolean
        @return: true if the item entered, false if it exited, None if it was unaffected
        """
        #@@@ in prep for n-way intersect
        return reduce((lambda x,y: x and y), [ x.changed(item, attribute) for x in self.__plans ])

    def monitored(self, op, item, attribute, *args, **kwds):
        return self.changed(item, attribute, op)

class DifferencePlan(LogicalPlan):
    """
    Logical plan which implements for queries
    """

    def __init__(self, item, ast):
        """
        constructor

        @param rep: a repository instance
        @type rep: Repository

        @param ast: an abstract syntax tree of the query
        @type ast: list
        """
        self.__item = item
        self.analyze(ast)

    def analyze(self, plans):
        """
        Produce a logical plan that corresponds to the 'difference' statement
        represented by the AST.
        (The AST is actually the list of arguments to 'difference')

        @param plans: a list of Logical Plans, one per arm of the difference statement
        @type plans: list
        """
        self.__plans = plans

    def execute(self):
        """
        Execute the query plan for a difference statement
        """
        plans = self.__plans
        log.debug(u"__execute_difference: plan = %s" % plans)
        s1 = sets.Set(plans[0].execute())
        s2 = sets.Set(plans[1].execute())
        return s1.difference(s2)

    def changed(self, item, attribute=None):
        """
        determine whether item has entered/exited the query result set

        @param item: an item that has been changed by commit
        @type item:

        @param attribute: the attribute on the item that was modified
        @type attribute:

        @rtype: boolean
        @return: true if the item entered, false if it exited, None if it was unaffected
        """
        flags = [ x.changed(item, attribute) for x in self.__plans ]
        return flags[0] and not flags[1]

    def monitored(self, op, item, attribute, *args, **kwds):
        return self.changed(item, attribute)

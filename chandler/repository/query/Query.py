
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.query.parser.QueryParser as QueryParser
import tools.timing
import sets
import mx.DateTime.ISO
from chandlerdb.util.UUID import UUID

import logging
log = logging.getLogger("RepoQuery")
log.setLevel(logging.INFO)

import time

class Query(object):

    def __init__(self, repo, queryString = None):
        """
        @param repo: The repository associated with the query @@@ replace with factory method
        @type repo: Repository
        
        @param queryString: A string containing the query to be processed
        @type queryString: string
        """
        log.debug("RepoQuery.__init__: ")
        self.__rep = repo
        self._view = self.__rep.view
        self.queryString = queryString
        self.args = {}
        self._kind = None
        self._logical_plan = None
        self._predicate = None
        self.recursive = True
        self._callbacks = {}

    def execute(self):
        """
        Compile this query

        Before calling compile, be sure that they queryString
        and any parameters have been set
        """
        
        start = time.time()
        if self.queryString is None:
            return
        log.debug("RepoQuery.compile(): %s" % self.queryString)

        if self.queryString:
            #tools.timing.reset()
            #tools.timing.begin("Parsing query")
            self.ast = QueryParser.parse('stmt', self.queryString)
            #tools.timing.end("Parsing query")
            log.debug("execute: AST = %s" % self.ast)
    
            #tools.timing.begin("Analyzing query")
            self._logical_plan = self.__analyze(self.ast)
            #tools.timing.end("Analyzing query")
            #tools.timing.results()
            log.debug("compile: %s:%f" % (self.queryString,time.time()-start))
        else:
            self._logical_plan = None

    def subscribe(self, callbackItem = None, callbackMethodName = None):
        """
        This query should subscribe to repository changes

        @param callbackItem: a Chandler Item that provides a callback method
        @type callbackItem: Item

        @param callbackMethodName: The name of the callback method on the callbackItem
        @type callbackMethodName: string
        """
        if callbackItem is not None:
            self._callbacks [callbackItem.itsUUID] = callbackMethodName
        log.debug("RepoQuery<>.subscribe(): %s" % (self.queryString))
        self.__rep.addNotificationCallback(self.queryCallback)
        
    def unsubscribe(self, callbackItem=None):
        """
        This query should stop subscribing to repository changes. If you don't specify a
        callbackItemUUID, all subscriptions will be removed.

        @param callbackItem: callbackItem to be removed
        @type callbackItem: Item
        """
        if callbackItem is None:
            self._callbacks = {}
        else:
            del self._callbacks [callbackItem.itsUUID]
        self.__rep.removeNotificationCallback(self.queryCallback)
        return len (self._callbacks)
    
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
        if self._view != view:
            return
        start = time.time()
        log.debug("RepoQuery.queryCallback for %s" % self.queryString)
        if self.queryString is None or self.queryString == "":
            return
        elif self._logical_plan is None and self.queryString is not None:
            self.execute()
        changed = False
        for uuid, reason, kwds in changes:
            i = view.findUUID(uuid)
            #@@@ there's a big problem with this if there are paths through multiple items -- we're going to need something fairly sophisticated here.
            if i is not None:
#                log.debug("RepoQuery.queryCallback %s:%s:%s" % (i, i.itsKind, self._kind))
                flag = self._logical_plan.changed(i)
                if flag is not None:
                    changed = True
                    if flag:
                        action = "entered"
                    else:
                        action = "exited"
                    break #@@@ this means we stop after 1 item (like old code) efficient, but wrong
        if changed:
            log.debug("RepoQuery.queryCallback: %s %s query result" % (uuid, action))
            for callbackUUID in self._callbacks.keys():
                item = view.find (callbackUUID)
                method = getattr (type(item), self._callbacks [callbackUUID])
                method (item, action)
        log.debug("queryCallback: %s:%f" % (self.queryString, time.time()-start))

    def __iter__(self):
        """
        Return a generator of the query results
        """
        if self._logical_plan is None and self.queryString is not None:
            self.execute()
        if self._logical_plan is not None:
            for i in self._logical_plan.execute():
                yield i
        else: # queries without plans are empty
            for i in []:
                yield i
                
    def __analyze(self, ast):
        """
        Produce a logical level query plan for the AST
        
        @param ast: A list (tree) containg the AST tree
        @type ast: list
        """                   
        log.debug("__analyze %s" % ast)
        op = ast[0]

        if op == 'for':
            #@@@ recursive handling is a problem now, just like args
            plan = ForPlan(self.__rep, ast[1:], self.args, self.recursive)
        elif op == 'union':
            plans = [ self.__analyze(i) for i in ast[1:][0] ]
            plan = UnionPlan(self.__rep, plans)
        elif op == 'intersect':
            plans = [ self.__analyze(i) for i in ast[1:][0:2] ]
            plan = IntersectionPlan(self.__rep, plans)
        elif op == 'difference':
            plans = [ self.__analyze(i) for i in ast[1:][0:2] ]
            plan = DifferencePlan(self.__rep, plans)
        else:
            raise ValueError, "Unrecognized operator %s" % op

        return plan


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
    def __init__(self, rep, ast, args, recursive):
        """
        constructor

        @param rep: a repository instance
        @type rep: Repository

        @param ast: an abstract syntax tree of the query
        @type ast: list

        @param args: the set of query parameters/arguments
        @type arts: dict

        @param recursive: whether or not a Kind based query is recursive over subkinds
        @type recursive: boolean
        """
        self.__rep = rep
        self.args = args #@@@ AUAUGUGUGH
        self.recursive = recursive
        self._pathKinds = {}
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
        kind = self.__rep.findPath(name)
        if kind is not None:
            return ('kind', kind)

        # $argument
        if name.startswith('$'): 
            itemUUID, attribute = self.args[name]
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
            log.debug("infix op: %s %s" % (op, args))
            return "%s %s %s" % (self.compile_predicate(args[0]), op, self.compile_predicate(args[1]))

        log.debug("compile_predicate: ast=%s, ast[0]=%s" % (ast,ast[0]))
        # function
        if ast[0] == 'fn':
            tok = ast[0]
            fn = ast[1]
            args = ast [2:][0]
            log.debug("%s %s %s" % (tok, fn, args))
            if fn in unary_fns and len(args) == 1:
                if fn == 'date':
                    pred = "mx.DateTime.ISO.ParseDateTime(%s)" % self.compile_predicate(args[0])
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
        elif ast[0] in unary_ops and len(ast[1:]) == 1:
            pred = "%s %s" % (ast[0], self.compile_predicate(ast[1]))
            return pred
        # infix operators
        elif ast[0] in infix_ops:
            args = ast[1:]
            return infix_op(ast[0],[args[0],args[1]])
        # path expression
        elif ast[0] == 'path': 
            # handle path expressions by computing the set of kinds/types covered
            # by the attributes along a path.  changed() will check commit against
            # this list of types to do incremental checking of multi-item paths

            #@@@ do iteration variable checks
            source = self.lookup_source(self.iter_source)
            path_type = source[0]

            if path_type == 'kind':
                current = source[1]
                count = 1
                # walk path, building reverse lookup to be used by changed()
                for i in ast[1][1:]:
                    try:
                        if (i.startswith('its')): #@@@ is this right?
                            attr = getattr(current, i)
                        else:
                            attr = current.getAttribute(i)
                    except AttributeError:
                        #@@@ raise a compilation error?
                        #@@@What about the case wher only some items only have the attr?
                        break

                    # stop at literal attributes
                    if type(attr) == str or type(attr) == unicode:
                        break
                    if attr.hasAttributeValue('otherName'):
                        if attr.hasAttributeValue(attr.otherName):
                            #@@@ need to handle list cardinality!
                            current = attr.getAttributeValue(attr.otherName).first()
                        else:
                            current = current.getAttribute(i).type
                        #@@@ this needs to generalize to multiple path expressions per predicate
                        self._pathKinds[current] = (attr.otherName, count)
            return '.'.join(ast[1])
        # other methods
        elif ast[0] == 'method':
            path = ast[1]
            args = ast[2]
            #@@@ check method name against approved list
            return  '.'.join(path[1])+"("+','.join(args)+")"
        # string constant or iteration variable or parameter ($1)
        elif type(ast) == str or type(ast) == unicode: 
            #@@@ check that ast != iteration variable, or parameter
            if ast.startswith('$'):
                arg = self.args[int(ast[1:])]
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
        log.debug("analyze_for: %s" % ast)
        
        self.iter_var = ast[0]
        self.iter_source = ast[1]
        predicate = ast[2]
        
        log.debug("analyze_for: var = %s, source = %s, predicate = %s" % (self.iter_var, self.iter_source, predicate))
        
        self.collection = self.lookup_source(self.iter_source)
        self.closure = self.compile_predicate(predicate) #@@@ duplicate
        self._predicate = self.closure
        
        log.debug("analyze_for: collection = %s, closure = %s" % (self.collection, self.closure))
            
        self.plan= (self.collection, compile(self.closure,'<string>','eval'))

    def execute(self):
        """
        Execute the query plan for a for statement
        """
        source = self.plan[0]

        # source is full text
        if type(source) == tuple and source[0] == 'ftcontains': 
            args = source[1]
            textItems = self.__rep.searchItems(args[0])
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
        elif source[0] == 'kind':
            self._kind = source[1]
            self._predicate = self.plan[1]

            import repository.item.Query as RepositoryQuery
            items = RepositoryQuery.KindQuery(recursive=self.recursive).run([source[1]])
        # source is an argument (ref-collection)
        elif source[0] == 'argsrc':
            items = self._getSourceIterator(source)
        elif source[0] == 'arg':
            items = source[1]
        else:
            assert False, "ForPlan.execute couldn't handle %s " % str(source)

        for i in items:
            try:
                if eval(self._predicate):
                    yield i
            except AttributeError:
                #@@@ log
                pass

    def _getSourceIterator(self, source):
        if len(source) == 3:
            arg, uuid, attrName = source
        else:
            arg, uuid = source
            attrName = None
        item = self.__rep.findUUID(uuid)
        if attrName:
            items = item.getAttributeValue(attrName)
        else:
            items = item
        return items

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
        if self._pathKinds.has_key(i.itsKind):
            # the item may be in the middle of a path expression
            # so try to walk backwards until we reach the kind that is the root of the query
            kind, count = self._pathKinds[i.itsKind]
            right_i = i
            for x in range(count):
                right_i = right_i.getAttributeValue(self._pathKinds[right_i.itsKind][0])
            i = right_i

        # handle recursive queries
        if self.recursive:
            rightKind = i.isItemOf(self._kind)
        else:
            rightKind = i.itsKind is self._kind

        if rightKind:
            result = eval(self._predicate)
        else:
            result = None

        #log.debug("changed: %s, %s" % (i, result))
        return result

class UnionPlan(LogicalPlan):
    """
    Logical plan which implements for queries
    """

    def __init__(self, rep, ast):
        """
        constructor

        @param rep: a repository instance
        @type rep: Repository

        @param ast: an abstract syntax tree of the query
        @type ast: list
        """
        self.__rep = rep
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
        log.debug("__execute_union: plan = %s" % plans)
        
        #@@@ DANGER - hack for self._kind - fix with notification upgrade
        self._kind = None

        s = sets.Set(plans[0].execute())
        for p in plans[1:]:
            s1 = sets.Set(p.execute())
            s.union_update(s1)
        return s
        
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
        bools = [ x.changed(item, attribute) for x in self.__plans ]
        bools = [ x for x in bools if x is not None ]
        if bools != []:
            return reduce((lambda x,y: x or y), bools)
        return None

    
class IntersectionPlan(LogicalPlan):
    """
    Logical plan which implements for queries
    """
    def __init__(self, rep, ast):
        """
        constructor

        @param rep: a repository instance
        @type rep: Repository

        @param ast: an abstract syntax tree of the query
        @type ast: list
        """
        self.__rep = rep
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
        log.debug("__execute_intersect: plan = %s" % plans)
        self._kind = None
        s1 = sets.Set(plans[0].execute())
        s2 = sets.Set(plans[1].execute())
        return s1.intersection(s2)

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
        #@@@ in prep for n-way intersect
        return reduce((lambda x,y: x and y), [ x.changed(item, attribute) for x in self.__plans ])



class DifferencePlan(LogicalPlan):
    """
    Logical plan which implements for queries
    """

    def __init__(self, rep, ast):
        """
        constructor

        @param rep: a repository instance
        @type rep: Repository

        @param ast: an abstract syntax tree of the query
        @type ast: list
        """
        self.__rep = rep
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
        log.debug("__execute_difference: plan = %s" % plans)
        self._kind = None
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


__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.query.parser.QueryParser as QueryParser
import tools.timing
import sets
import mx.DateTime.ISO

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
        self.queryString = queryString
        self.args = []
        self._kind = None
        self._logical_plan = None
        self._predicate = None
        self.recursive = True

    def execute(self):
        """
        Execute this query

        Before calling execute, be sure that they queryString
        and any parameters have been set
        """
        
        start = time.time()
        if self.queryString is None:
            return
        log.debug("RepoQuery.execute(): %s" % self.queryString)

#        tools.timing.reset()
        tools.timing.begin("Parsing query")
        if self.queryString is None:
            raise ValueError, "queryString for %s is None" % self.itsUUID
        self.ast = QueryParser.parse('stmt', self.queryString)
        tools.timing.end("Parsing query")
        log.debug("execute: AST = %s" % self.ast)

        tools.timing.begin("Analyzing query")
        self._logical_plan = self.__analyze(self.ast)
        tools.timing.end("Analyzing query")
#        tools.timing.results()
        log.debug("execute: %s:%f" % (self.queryString,time.time()-start))

    def subscribe(self):
        """
        This query should subscribe to repository changes
        """
        log.debug("RepoQuery<>.subscribe(): %s" % (self.queryString))
        self.__rep.addNotificationCallback(self.queryCallback)
        
    def unsubscribe(self):
        """
        This query should stop subscribing to repository changes
        """
        self.__rep.removeNotificationCallback(self.queryCallback)
    
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
        start = time.time()
        log.debug("RepoQuery.queryCallback for %s" % self.queryString)
        if self.queryString is None:
            return
        elif self._logical_plan is None and self.queryString is not None:
            self.execute()
        changed = False
        for uuid, reason, kwds in changes:
            i = view.findUUID(uuid)
            #@@@ there's a big problem with this if there are paths through multiple items -- we're going to need something fairly sophisticated here.
            if i is not None:
#                log.debug("RepoQuery.queryCallback %s:%s" % (i, i.itsKind))
                if self.recursive:
                    rightKind = i.isItemOf(self._kind)
                else:
                    rightKind = i.itsKind is self._kind
                if rightKind:
                    changed = True
                    #@@@ accumulate batch results
                    if eval(self._predicate):
                        action = "entered"
                    else:
                        action = "exited"
                    break #@@@ this means we stop after 1 item (like old code) efficient, but wrong
        if changed:
            log.debug("RepoQuery.queryCallback: %s %s query result" % (uuid, action))
            view.findPath('//parcels/osaf/framework/query_changed').Post( {'query' : i.itsUUID, 'action': action} )
        log.debug("queryCallback: %s:%f" % (self.queryString, time.time()-start))

    def __iter__(self):
        """
        Return a generator of the query results
        """
        if self._logical_plan is None and self.queryString is not None:
            self.execute()
        if self._logical_plan is not None:
            for i in self.__executePlan(self._logical_plan):
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
        
        def lookup_source(name):
            """
            Convert the name of a source to a collection
            @@@ ATM this returns a kind to be used w/ KindQuery -
                this needs to be generalized to any ref collection
            """
            #@@ don't enclose kind paths in ""
            if (name.startswith('"') and name.endswith('"')) or \
               (name.startswith("'") and name.endswith("'")):
                name = name[1:-1]
            kind = self.__rep.findPath(name)
            if kind is not None:
                return ('kind', kind)
            if name.startswith('$'): # variable argument
                return ('arg',self.args[int(name[1:])-1])
            assert False, "lookup_source couldn't handle %s" % name

        def compile_predicate(ast):
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
                return "%s %s %s" % (compile_predicate(args[0]), op, compile_predicate(args[1]))

            log.debug("compile_predicate: ast=%s, ast[0]=%s" % (ast,ast[0]))
            if ast[0] == 'fn': # function
                tok = ast[0]
                fn = ast[1]
                args = ast [2:][0]
                log.debug("%s %s %s" % (tok, fn, args))
                if fn in unary_fns and len(args) == 1:
                    if fn == 'date':
                        pred = "mx.DateTime.ISO.ParseDateTime(%s)" % compile_predicate(args[0])
                    else:
                        pred = "%s(%s)" % (fn, compile_predicate(args[0]))
                elif fn in binary_fns and len(args) == 2: 
                    pred = fn+'('+compile_predicate(args[0])+','+compile_predicate(args[1])+')'
                elif fn in infix_fns:
                    if fn == 'contains':
                        pred = infix_op('in', [args[1],args[0]])
                    else:
                        pred = infix_op(fn, [args[0], args[1]])
                else:
                    assert False, "unhandled fn %s" % fn
                return pred
            elif ast[0] in unary_ops and len(ast[1:]) == 1:
                pred = "%s %s" % (ast[0], compile_predicate(ast[1]))
                return pred
            elif ast[0] in infix_ops:
                args = ast[1:]
                return infix_op(ast[0],[args[0],args[1]])
            elif ast[0] == 'path': # path expression
                #@@@ do iteration variable checks
                return '.'.join(ast[1])
            elif ast[0] == 'method':
                path = ast[1]
                args = ast[2]
                #@@@ check method name against approved list
                return  '.'.join(path[1])+"("+','.join(args)+")"
            elif type(ast) == str or type(ast) == unicode: # string constant or iteration variable or parameter ($1)
                #@@@ check that ast != iteration variable, or parameter
                return ast
            assert False, "unhandled predicate: operator=%s, args=%s, type(args)=%s" % (op, ast, type(ast))
                
        def analyze_for(ast):
            """
            Produce a logical plan (collection name, compiled predicate) that
            corresponds to the 'for' statement represented by the AST.
            (The AST is actually the arguments to 'for')

            @param ast:
            @type ast: list
            """
            log.debug("analyze_for: %s" % ast)

            iter_var = ast[0]
            iter_source = ast[1]
            predicate = ast[2]

            log.debug("analyze_for: var = %s, source = %s, predicate = %s" % (iter_var, iter_source, predicate))

            collection = lookup_source(iter_source)
            closure = compile_predicate(predicate)
            self._predicate = closure

            log.debug("analyze_for: collection = %s, closure = %s" % (collection, closure))
            
            return ('for', (collection, compile(closure,'<string>','eval')))

        def analyze_union(ast):
            """
            Produce a logical plan that corresponds to the 'union' statement
            represented by the AST.
            (The AST is actually the list of arguments to 'union')
            """
            queries = [ self.__analyze(i) for i in ast[0] ]
            return ('union', queries)

        def analyze_intersect(ast):
            """
            Produce a logical plan that corresponds to the 'intersect' statement
            represented by the AST
            (The AST is the two arguments to 'intersect')
            """
            queries = [ self.__analyze(i) for i in ast[0:2] ]
            return ('intersect', queries)

        def analyze_difference(ast):
            """
            Produce a logical plan that corresponds to the 'difference'
            statement represented by the AST
            (The AST is the two arguments to 'difference')
            """
            queries = [ self.__analyze(i) for i in ast[0:2] ]
            return ('difference', queries)


        log.debug("__analyze %s" % ast)
        op = ast[0]

        if op == 'for':
            plan = analyze_for(ast[1:])
        elif op == 'union':
            plan = analyze_union(ast[1:])
        elif op == 'intersect':
            plan = analyze_intersect(ast[1:])
        elif op == 'difference':
            plan = analyze_difference(ast[1:])
        else:
            raise ValueError, "Unrecognized operator %s" % op

        return plan

    def __execute_for(self, plan):
        """
        Execute the query plan for a for statement
        @param: plan
        @type param: tuple (source collection, compiled predicate)
        """
        source = plan[0]

        if source[0] == 'kind':
            self._kind = source[1]
            self._predicate = plan[1]

            import repository.item.Query as RepositoryQuery
            items = RepositoryQuery.KindQuery(recursive=self.recursive).run([source[1]])
        else: # it = 'arg'
            items = source[1]

        for i in items:
            if eval(self._predicate):
                yield i

    def __execute_union(self, plans):
        """
        Execute the query plan for a union statement
        @param: plans
        @type param: list (plans to union)
        """
        log.debug("__execute_union: plan = %s" % plans)
        
        #@@@ DANGER - hack for self._kind - fix with notification upgrade
        self._kind = None

        s = sets.Set(self.__executePlan(plans[0]))
        for p in plans[1:]:
            s1 = sets.Set(self.__executePlan(p))
            s.union(s1)
        return s
        
#        for p in plans:
#            print p
#            for i in self.__executePlan(p):
#                print i
#                yield i

    def __execute_intersect(self, plans):
        """
        Execute the query plan for an intersect statement
        @params: plans
        @type param: list (two plans)
        """
        log.debug("__execute_intersect: plan = %s" % plans)
        self._kind = None
        s1 = sets.Set(self.__executePlan(plans[0]))
        s2 = sets.Set(self.__executePlan(plans[1]))
        return s1.intersection(s2)

    def __execute_difference(self, plans):
        """
        Execute the query plan for a difference statement
        @params: plans
        @type param: list (two plans)
        """
        log.debug("__execute_difference: plan = %s" % plans)
        self._kind = None
        s1 = sets.Set(self.__executePlan(plans[0]))
        s2 = sets.Set(self.__executePlan(plans[1]))
        return s1.difference(s2)

    def __executePlan(self, plan):
        """
        Execute a logical query plan (a tuple of the collection to be queried
        and a compiled query predicate)

        @@@ at the moment, the collection is just the name of the kind for KindQuery

        @param plan: a tuple indicating the plan type, and a plan
        @type param: tuple 
        """
        start = time.time()
        if plan[0] == 'for':
            return self.__execute_for(plan[1])
        elif plan[0] == 'union':
            return self.__execute_union(plan[1])
        elif plan[0] == 'intersect':
            return self.__execute_intersect(plan[1])
        elif plan[0] == 'difference':
            return self.__execute_difference(plan[1])
        else:
            raise ValueError, "Unrecognized plan %s" % plan[0]
        log.debug("__executePlan %s:%f", (self.queryString % time.time()-start))

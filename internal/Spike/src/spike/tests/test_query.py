"""Unit tests for query system internals"""

from unittest import TestCase
from spike.schema import Entity
from spike.query import *
from spike.models import Set
import operator

def divisible_by(num):
    return expression("not ob % "+str(num), "ob")


class TestBasicFilters(TestCase):

    def test_basics(self):
        # An abstract filter's conjuncts and disjuncts should be itself
        f = AbstractFilter()
        conj, = f.conjuncts()
        disj, = f.disjuncts()
        self.failUnless(conj is f)
        self.failUnless(disj is f)

    def test_inverse_algebra(self):
        # ~~f is f, ~f is not f, ~Inverter(f) is f
        f = AbstractFilter()
        self.failIf(~f is f)
        self.failUnless(~~f is f)
        self.failUnless((~NotFilter(f)) is f)
        self.assertEqual(~f,NotFilter(f))

    def test_inverse_comparison(self):
        f = AbstractFilter()
        g = AbstractFilter()

        # Inverters compare equal to other inverters with same input
        self.assertEqual(NotFilter(f),NotFilter(f))
        # But unequal to ones with different input
        self.assertNotEqual(NotFilter(f),NotFilter(g))
        # Or to non-inverters
        self.assertNotEqual(NotFilter(f),f)

    def check_boolean_algebra(self,cls,flatten_method,op):
        """Utility routine to test binary operators"""

        f = AbstractFilter()
        e = divisible_by(2)
        t = divisible_by(3)

        def flattened(ob):
            return set(getattr(ob,flatten_method)())

        # Trivial cases of only one set being combined
        self.failUnless(cls(f) is f)
        self.failUnless(cls(f,f) is f)

        # A combination's flat form is its inputs in the simple case
        self.assertEqual(flattened(cls(e,t)), set([e,t]))
        self.assertEqual(flattened(op(e,t)), set([e,t]))

        # And a combination should equal a combination of the same primitives
        self.assertEqual(cls(e,t), cls(t,e))
        self.assertEqual(cls(e,cls(t,f)), cls(e,f,t))

        # but not equal different ones
        self.assertNotEqual(cls(e,t), cls(t,f))

        # Combination should also be associative
        for inp in [
            cls(cls(e,t),f), cls(e,cls(t,f)), cls(e,t,f),
            op(op(e,t),f), op(e,op(t,f)),
        ]:
            self.assertEqual(flattened(inp), set([e,t,f]))

            # And negative logic transforms should apply to conjuncts/disjuncts
            self.assertEqual(
                set((~inp).conjuncts()), set(~i for i in inp.disjuncts())
            )

            self.assertEqual(
                set((~inp).disjuncts()), set(~i for i in inp.conjuncts())
            )

    def test_intersect_algebra(self):
        self.check_boolean_algebra(AndFilter,"conjuncts",operator.and_)

    def test_union_algebra(self):
        self.check_boolean_algebra(OrFilter,"disjuncts",operator.or_)

    def test_contains(self):
        even = divisible_by(2)
        self.failUnless(2 in even)
        self.failIf(1 in even)
        self.failUnless(1 in ~even)
        self.failIf(2 in ~even)

    def test_inverse_junctions(self):
        f = AbstractFilter()
        self.assertEqual(
            list(NotFilter(f).conjuncts()), [~i for i in f.disjuncts()]
        )
        self.assertEqual(
            list(NotFilter(f).disjuncts()), [~i for i in f.conjuncts()]
        )

    def test_intersect(self):
        # Intersection of no sets is intersection identity, i.e. "true"
        self.failUnless(1 in AndFilter())

        # Intersection of one set is that set.
        i = AndFilter(divisible_by(2))
        self.failIf(1 in i)
        self.failUnless(2 in i)

        i = AndFilter(divisible_by(3))
        self.failIf(1 in i)
        self.failIf(2 in i)
        self.failUnless(3 in i)

        i = AndFilter(divisible_by(2),divisible_by(3))
        for j in range(1,6):
            self.failIf(j in i)
        self.failUnless(6 in i)

    def test_union(self):
        # Union of no sets is union identity, i.e. "empty set"
        self.failIf(1 in OrFilter())

        # Union of one set is that set.
        i = OrFilter(divisible_by(2))
        self.failIf(1 in i)
        self.failUnless(2 in i)

        i = OrFilter(divisible_by(3))
        self.failIf(1 in i)
        self.failIf(2 in i)
        self.failUnless(3 in i)

        i = OrFilter(divisible_by(2),divisible_by(3))
        self.failIf(1 in i)
        self.failUnless(2 in i)
        self.failUnless(3 in i)

    def test_subtraction(self):
        two_or_three = divisible_by(2)|divisible_by(3)
        two_or_three_less_six = two_or_three -divisible_by(6)
        self.assertEqual(
            [2,3,4,8,9],  # numbers divisible by 2 or 3 but not six
            filter(two_or_three_less_six.__contains__, range(10))
        )

    def test_class_filters(self):
        # schema classes are query filters, with all the trimmings

        class MyEntity(Entity):
            pass

        any_but_mine = Entity - MyEntity

        self.failIf(Entity() in MyEntity)
        self.failUnless(MyEntity() in MyEntity)
        self.failIf(MyEntity() in any_but_mine)
        self.failUnless(Entity() in any_but_mine)
        self.failIf(MyEntity() in ~MyEntity)

    def test_set_filters(self):
        # Sets are also usable as filters
        s1 = Set([1,2,3])
        s2 = Set([4,5])
        self.failUnless(9 not in s1)
        self.failUnless(2 not in ~s1)
        self.failUnless(4 in s1|s2)



































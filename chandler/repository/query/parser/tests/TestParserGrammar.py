__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Founation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#
# doctest based tests for Chandler query parser
#

def test():
  """
  ## VALUE_EXPRs
  # positive tests
  >>> print parse('value_expr','abc')
  abc
  >>> print parse('value_expr','f()')
  f
  >>> print parse('value_expr','f(1,2)')
  ['fn', 'f', ['1', '2']]
  >>> print parse('value_expr','x.y.z')
  ['path', ['x', 'y', 'z'], None]

  # negative tests
  >>> print parse('value_expr','+')
  None
  >>> print parse('value_expr','f(')
  None

  #this is really bad error handling in yapps
  >>> print parse('value_expr','2a')
  2

  # print parse('value_expr','x.y.z.f(1,2)')

  ## UNARY_EXPR
  >>> print parse('unary_expr','abc')
  abc
  >>> print parse('unary_expr','-1')
  ['-', '1']

  # syntatically legal, but type illegal
  >>> print parse('unary_expr','-abc')
  ['-', 'abc']

  ## MUL_EXPR
  >>> print parse('mul_expr','abc')
  abc
  >>> print parse('mul_expr','-1')
  ['-', '1']
  >>> print parse('mul_expr','a * b')
  ['*', 'a', 'b']
  >>> print parse('mul_expr','x.y.z * a')
  ['*', ['path', ['x', 'y', 'z'], None], 'a']
  >>> print parse('mul_expr','a/b')
  ['/', 'a', 'b']
  >>> print parse('mul_expr','a div b')
  ['div', 'a', 'b']
  >>> print parse('mul_expr','a mod b')
  ['mod', 'a', 'b']


  ## ADD_EXPR
  >>> print parse('add_expr','abc')
  abc
  >>> print parse('add_expr','-1')
  ['-', '1']
  >>> print parse('add_expr','a + b')
  ['+', 'a', 'b']
  >>> print parse('add_expr','a - b')
  ['-', 'a', 'b']
  >>> print parse('add_expr','a + b * c')
  ['+', 'a', ['*', 'b', 'c']]
  >>> print parse('add_expr','a * d + b * c')
  ['+', ['*', 'a', 'd'], ['*', 'b', 'c']]

  ## REL_EXPR
  >>> print parse('rel_expr','abc')
  abc
  >>> print parse('rel_expr','-1')
  ['-', '1']
  >>> print parse('rel_expr','a + b')
  ['+', 'a', 'b']
  >>> print parse('rel_expr','a + b * c')
  ['+', 'a', ['*', 'b', 'c']]
  >>> print parse('rel_expr','a * d + b * c')
  ['+', ['*', 'a', 'd'], ['*', 'b', 'c']]
  >>> print parse('rel_expr','a == b')
  ['==', 'a', 'b']
  >>> print parse('rel_expr','a != b')
  ['!=', 'a', 'b']
  >>> print parse('rel_expr','a > b')
  ['>', 'a', 'b']
  >>> print parse('rel_expr','a < b')
  ['<', 'a', 'b']
  >>> print parse('rel_expr','a >= b')
  ['>=', 'a', 'b']
  >>> print parse('rel_expr','a <= b')
  ['<=', 'a', 'b']
  >>> print parse('rel_expr','a == b * c')
  ['==', 'a', ['*', 'b', 'c']]
  >>> print parse('rel_expr','a + d  == b * c')
  ['==', ['+', 'a', 'd'], ['*', 'b', 'c']]

  ## AND_OR_EXPR
  >>> print parse('and_or_expr','abc')
  abc
  >>> print parse('and_or_expr','-1')
  ['-', '1']
  >>> print parse('and_or_expr','a + b')
  ['+', 'a', 'b']
  >>> print parse('and_or_expr','a + b * c')
  ['+', 'a', ['*', 'b', 'c']]
  >>> print parse('and_or_expr','a * d + b * c')
  ['+', ['*', 'a', 'd'], ['*', 'b', 'c']]
  >>> print parse('and_or_expr','a == b')
  ['==', 'a', 'b']
  >>> print parse('and_or_expr','a != b')
  ['!=', 'a', 'b']
  >>> print parse('and_or_expr','a == b * c')
  ['==', 'a', ['*', 'b', 'c']]
  >>> print parse('and_or_expr','a + d  == b * c')
  ['==', ['+', 'a', 'd'], ['*', 'b', 'c']]
  >>> print parse('and_or_expr','a == b and c > d')
  ['and', ['==', 'a', 'b'], ['>', 'c', 'd']]
  >>> print parse('and_or_expr','a == b or c > d')
  ['or', ['==', 'a', 'b'], ['>', 'c', 'd']]

  ## FOR_EXPR
  >>> print parse('for_stmt','for i in x where i.name == "id"')
  ['for', 'i', 'x', ['==', ['path', ['i', 'name'], None], '"id"']]
  >>> print parse('for_stmt', "for i in '//userdata/zaobaoitems' where i.channel.creator == 'Ted Leung'")
  ['for', 'i', "'//userdata/zaobaoitems'", ['==', ['path', ['i', 'channel', 'creator'], None], "'Ted Leung'"]]
  >>> print parse('for_stmt','for i in z where i.price < 10 and i.color == "green"')
  ['for', 'i', 'z', ['and', ['<', ['path', ['i', 'price'], None], '10'], ['==', ['path', ['i', 'color'], None], '"green"']]]
  >>> print parse('for_stmt', 'for i in z where len(z.messages) > 1000')
  ['for', 'i', 'z', ['>', ['fn', 'len', [['path', ['z', 'messages'], None]]], '1000']]
  """
  pass

if __name__ == '__main__':
    import doctest, unittest, sys
#    from repository.query.parser.QueryParser import parse
#    sys.exit(doctest.testmod()[0])


__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Founation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

###
### Parser for Chandler query language
###

# helper functions
def if_none_set(var, expr1, expr2):
  """
  return expr1 if var is None else, expr2
  """
  if var is None:
    return expr1
  else:
    return expr2

def make_op(lhs, op, rhs):
  """
  Make a binary operator list, in prefix form
  """
  return [op, lhs, rhs]


%%
parser Query:
    ignore:    "[ \r\t\n]+"
    token NUM: '[0-9]+'
    token FOR: '[Ff][Oo][Rr]'
    token ID: '[a-zA-Z]+'
    token STRING: '"([^\\"]+|\\\\.)*"|\'([^\']+|\\\\.)*\''
    token UNOP: '[+-]'
    token MULOP: '(\*|/|div|mod)'
    token ADDOP: '(\+|-)'
    token RELOP: '(==|!=|>=|<=|>|<)'
    token BOOLOP: '(and|or)'
    token END: '$'

    rule for_stmt: 'for' ID 'in' 
                   ( name_expr 'where' and_or_expr 
                     {{ return [ 'for', ID, name_expr, and_or_expr ] }} END 
                   | STRING 'where' and_or_expr 
                     {{ return [ 'for', ID, STRING, and_or_expr ] }} END )

    rule and_or_expr: rel_expr
         {{ result = rel_expr }}
         [ BOOLOP rel_expr {{ result = make_op(result, BOOLOP, rel_expr) }}]
         {{ return result }}
    
    rule rel_expr: add_expr
         {{ result = add_expr }}
         [ RELOP add_expr {{ result = make_op(result, RELOP, add_expr) }} ]
         {{ return result }}

    rule add_expr: mul_expr
         {{ result = mul_expr}}
         [ ADDOP mul_expr {{ result = make_op(result, ADDOP, mul_expr) }}]
         {{ return result }}

    rule mul_expr: unary_expr
         {{ result = unary_expr }}
         [ MULOP unary_expr {{ result = make_op(result, MULOP, unary_expr);}} ]
         {{ return result }}
    
    rule unary_expr: {{ UNOP = None }} [ UNOP ] value_expr
         {{ return if_none_set(UNOP,value_expr,[ UNOP, value_expr ]) }}

    rule value_expr: constant {{ return constant }}
         | ID {{ result = ID }}
           [ "\(" [ arg_list {{ result = make_op(result,'fn',arg_list) }} ] '\)'
            | {{ result = [result] }} ("\." ID {{ result.append(ID) }} )+
              {{ result = make_op(result,'path',None) }}
           ]
         {{ return result }}

    rule constant: STRING {{ return STRING }}
                   | NUM {{ return NUM }}
    
    rule arg_list:  and_or_expr {{ result = [and_or_expr] }} 
                    ( ',' and_or_expr {{ result.append(and_or_expr) }} )*
                    {{ return result }}

    rule name_expr: ID {{ return ID }}

%%

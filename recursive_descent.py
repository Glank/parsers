# An example of a recursive descent parser.

import re

from tokenizer import tokenize, is_token_name
from utils import print_parse_node

RULES = [
  ('expression', ['sum']),
  ('value', ['(', 'expression', ')']),
  ('value', ['number']),
  ('value', ['-', 'value']),
  ('product', ['value', 'product*']),
  ('product*', ['*', 'value', 'product*']),
  ('product*', ['/', 'value', 'product*']),
  ('product*', ['empty']),
  ('sum', ['product', 'sum*']),
  ('sum*', ['+', 'product', 'sum*']),
  ('sum*', ['-', 'product', 'sum*']),
  ('sum*', ['empty']),
]

def _parse(rule, tokens, offset, stack_depth=0):
  # Uncomment the following lines to see how the parsing happens.
  # print('{}rule: {}'.format(' '*stack_depth, rule))
  # print('{}on: {}'.format(' '*stack_depth, tokens[offset:]))
  rule_head, rule_tail = rule
  matched_symbols = []
  for symbol in rule_tail:
    if symbol == 'empty':
      continue
    elif is_token_name(symbol):
      if offset >= len(tokens):
        return None, offset
      if tokens[offset][0] == symbol:
        matched_symbols.append(tokens[offset])
        offset += 1
      else:
        return None, offset
    else:
      found = False
      for sub_rule in RULES:
        if sub_rule[0] == symbol:
          match, new_offset = _parse(sub_rule, tokens, offset, stack_depth+1)
          if match is not None:
            found = True
            offset = new_offset
            matched_symbols.append(match)
            break
      if not found:
        return None, offset 
  return (rule_head, matched_symbols), offset

def parse(tokens):
  for rule in RULES[:1]:
    match, offset = _parse(rule, tokens, 0)
    if match is not None:
      return match
  raise Exception("Could not parse tokens.")


def _children(parse_node):
  return parse_node[1]

def is_terminal(parse_node):
  return len(_children(parse_node)) == 0

BINARY_OPERATOR_ACCUMULATION_RULES = {
  '+': lambda a, v: ('num', a[1]+v[1]),
  '-': lambda a, v: ('num', a[1]-v[1]),
  '*': lambda a, v: ('num', a[1]*v[1]),
  '/': lambda a, v: ('num', a[1]/v[1]),
}
BINARY_OPERATOR_VALID_TYPES = {
  '+': ['num'],
  '-': ['num'],
  '*': ['num'],
  '/': ['num'],
}
BINARY_OPERATOR_NAMES = ['sum', 'product']

def evaluate(parse_node):
  node_type, node_children = parse_node
  if node_type == 'expression':
    assert len(node_children) == 1
    return evaluate(node_children[0])
  elif node_type in BINARY_OPERATOR_NAMES:
    # binary operators
    assert len(node_children) == 2
    accumulator = evaluate(node_children[0])
    rhs_node = node_children[1]
    while not is_terminal(rhs_node):
      rhs_children = _children(rhs_node)
      assert len(rhs_children) == 3
      rhs_type = rhs_children[0][0]
      rhs_value = evaluate(rhs_children[1])
      acc_rule = BINARY_OPERATOR_ACCUMULATION_RULES.get(rhs_type, None)
      valid_types = BINARY_OPERATOR_VALID_TYPES.get(rhs_type, None)
      if acc_rule is None or valid_types is None:
        raise Exception('Invalid binary operator: {}'.format(rhs_type))
      if rhs_value[0] not in valid_types:
        raise Exception('Invalid type for {}: {}'.format(rhs_type, rhs_value))
      accumulator = acc_rule(accumulator, rhs_value)
      rhs_node = rhs_children[2]
    return accumulator
  elif node_type == 'value':
    #('value', ['number']),
    if len(node_children) == 1:
      return evaluate(node_children[0])
    #('value', ['-', 'value']),
    elif len(node_children) == 2:
      return -evaluate(node_children[1])
    #('value', ['(', 'expression', ')']),
    elif len(node_children) == 3:
      return evaluate(node_children[1])
    else:
      raise Exception('Invalid value node: {}'.format(node_children))
  elif node_type == 'number':
    value = node_children
    assert type(value) is str
    return ('num', float(value))
  else:
    raise Exception('Invalid input node type: {}'.format(node_type))

#for rule in RULES:
#  print(rule)

string = '3+4*5-7/2+1'
print('string: {}'.format(string))
tokens = list(tokenize(string))
print('tokens: {}'.format(tokens))

parse_node = parse(tokens)
print('parse_tree:\n----------')
print_parse_node(parse_node)

result = evaluate(parse_node)
print('result: {}'.format(result))

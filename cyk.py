# An example of a Cocke-Younger-Kasami parser.

import re

from tokenizer import tokenize, is_token_name
from utils import print_parse_node, print_grammar

BASE_RULES_1 = [
  ('expression', ['sum']),
  ('value', ['(', 'expression', ')']),
  ('value', ['number']),
  ('value', ['-', 'value']),
  ('product', ['value']),
  ('product', ['value', '*', 'product']),
  ('product', ['value', '/', 'product']),
  ('sum', ['product']),
  ('sum', ['product', '+', 'sum']),
  ('sum', ['product', '-', 'sum']),
]

BASE_RULES_2 = [
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

BASE_RULES_3 = [
  ('expression', ['foo']),
  ('foo', ['bar']),
  ('bar', ['+']),
]

BASE_RULES = BASE_RULES_1

# Rules must be in Chomsky Normal Form to work in a CYK parser
# https://en.wikipedia.org/wiki/Chomsky_normal_form
def to_cnf(start_symbol, rules):
  def is_nonterminal(name, rules):
    return any(head == name for head, _ in rules)

  def is_existing_name(name, rules):
    return is_nonterminal(name, rules) or is_token_name(name) or name=='empty'

  def new_name(base_name, rules):
    "Generate a new name that doesn't conflict with any others."
    if not is_existing_name(base_name, rules):
      return base_name
    m = re.match(r'^(.*[^0-9])([0-9]*)$', base_name)
    base = m.groups()[0]
    num = m.groups()[1]
    if num == '':
      num = -1
    else:
      num = int(num)
    num += 1
    template = '{}{}'
    next_try = template.format(base, num)
    while is_existing_name(next_try, rules):
      num += 1
      next_try = template.format(base, num)
    return next_try
    
  #print("START")
  # START: Eliminate the start symbol from right-hand sides
  new_start_symbol = new_name(start_symbol, rules)
  new_rules = [
    (new_start_symbol, [start_symbol]),
  ] + rules
  start_symbol = new_start_symbol
  rules = new_rules

  #print("TERM")
  # TERM: Eliminate rules with nonsolitary terminals
  new_rules = []
  for rule_head, rule_tail in rules:
    if len(rule_tail) == 1:
      new_rules.append((rule_head, rule_tail))
      continue
    if not any(is_token_name(a) or a=='empty' for a in rule_tail):
      new_rules.append((rule_head, rule_tail)) 
      continue
    new_tail = []
    for a in rule_tail:
      if not (is_token_name(a) or a=='empty'):
        new_tail.append(a)
      else:
        new_symbol = new_name(a, rules)
        if not is_existing_name(new_symbol, new_rules):
          new_rules.append((new_symbol, [a]))
        new_tail.append(new_symbol)
    new_rules.append((rule_head, new_tail))
  rules = new_rules

  #print("BIN")
  # BIN: Eliminate right-hand sides with more than 2 nonterminals
  new_rules = []
  for rule_head, rule_tail in rules:
    if len(rule_tail) <= 2:
      new_rules.append((rule_head, rule_tail))
      continue
    prev_symbol = rule_head
    cur_symbol = new_name(rule_head, rules+new_rules)
    for i in range(len(rule_tail)-2):
      new_rules.append((prev_symbol, [rule_tail[i], cur_symbol]))
      prev_symbol = cur_symbol
      cur_symbol = new_name(rule_head, rules+new_rules)
    new_rules.append((cur_symbol, [rule_tail[-2], rule_tail[-1]]))
  rules = new_rules

  #print("DEL")
  # DEL: Eliminate empty-rules
  nullable_set = set()
  # check if head produces empty
  for h, t in rules:
    if len(t) == 1 and t[0] == 'empty':
      nullable_set.add(h)
  # check if head prduces a string that is entirely nullable
  added_new = True
  while added_new:
    added_new = False
    for h, t in rules:
      for c in t:
        if not is_token_name(c) and c in nullable_set:
          if h not in nullable_set:
            nullable_set.add(h)
            added_new = True
          break
  def get_null_reduced_tails(tail):
    if len(tail)==0:
      yield []
      return
    if tail[0] in nullable_set:
      for t in get_null_reduced_tails(tail[1:]):
        yield t
        yield [tail[0]]+t
    else:
      for t in get_null_reduced_tails(tail[1:]):
        yield [tail[0]]+t
  new_rules = []
  for rule_head, rule_tail in rules:
    for new_tail in get_null_reduced_tails(rule_tail):
      if len(new_tail) == 0:
        new_rules.append((rule_head, ['empty']))
      else:
        new_rules.append((rule_head, new_tail))
  rules = new_rules
  # remove all null-only rules that aren't the start_symbol
  removed_any = True
  while removed_any:
    removed_any = False
    null_only = {'empty': True}
    for h, t in rules:
      if len(t) == 1 and t[0] == 'empty':
        null_only[h] = null_only.get(h, True) and True
      else:
        null_only[h] = False
    new_rules = []
    for h, t in rules:
      if null_only[h] and h != start_symbol:
        removed_any = True
      else:
        new_t = [s for s in t if not null_only.get(s, False)]
        if len(new_t) == 0:
          new_t = ['empty']
        new_rules.append((h,new_t))
    rules = new_rules
    # remove duplicates
    new_rules = []
    existance_sets = {}
    for h, t in rules:
      t_tup = tuple(t)
      existance_set = existance_sets.get(h, set())
      if t_tup in existance_set:
        removed_any = True
      else:
        existance_set.add(t_tup)
        existance_sets[h] = existance_set
        new_rules.append((h, t))
    rules = new_rules

  #print("UNIT")
  #print_grammar(rules)
  # UNIT: Eliminate unit rules
  while True:
    # Find the next non-terminal unit rule, U -> V
    unit_symbol = None
    for i, (h, t) in enumerate(rules):
      if len(t) == 1 and not (is_token_name(t[0]) or t[0]=='empty'):
        unit_symbol = t[0]
        break
    if unit_symbol is None:
      break
    #print('Unit symbol: {}'.format(unit_symbol))
    expansions = [t for r,t in rules if r==unit_symbol]
    # Replace all rules like
    # A -> U
    # with 
    # A -> *E1
    # A -> *E2
    # ...
    # And delete the rules U -> *En if U is not found
    # in the tails of any other rules which are not headed by U.
    new_rules = []
    delete_unit_head = True
    for h,t in rules:
      if len(t) == 1 and t[0] == unit_symbol:
        for e in expansions:
          new_rules.append((h, e))
      else:
        if h != unit_symbol and unit_symbol in t:
          delete_unit_head = False
        new_rules.append((h, t))
    rules = new_rules
    if delete_unit_head:
      rules = [(h,t) for h,t in rules if h != unit_symbol]
    #print('--------')
    #print_grammar(rules)

  #print("END")
  return start_symbol, rules

def cyk(tokens, cnf_rules, length_of_span, start_of_span, rule_index, memo):
  if start_of_span >= len(tokens):
    return None
  head, tail = cnf_rules[rule_index]
  if length_of_span == 1:
    if len(tail) != 1:
      return None
    if tokens[start_of_span][0] == tail[0]:
      return (head, [tokens[start_of_span]])

  memo_key = (length_of_span, start_of_span, rule_index)
  if memo_key in memo:
    return memo[memo_key]
  
  if len(tail) == 1:
    return None
  assert len(tail) == 2  #otherwise not cnf

  lhs_match = None
  lhs_length = length_of_span
  while lhs_match is None and lhs_length > 1:
    lhs_length -= 1
    for i, (h,t) in enumerate(cnf_rules):
      if h == tail[0]:
        lhs_match = cyk(tokens, cnf_rules, lhs_length, start_of_span, i, memo=memo)
        if lhs_match is not None:
          break
  if lhs_match is None:
    memo[memo_key] = None
    return None

  rhs_match = None
  for i, (h,t) in enumerate(cnf_rules):
    if h == tail[1]:
      rhs_match = cyk(tokens, cnf_rules, length_of_span-lhs_length, start_of_span+lhs_length, i, memo=memo)
      if rhs_match is not None:
        break
  if rhs_match is None:
    memo[memo_key] = None
    return None

  result = (head, [lhs_match, rhs_match])
  memo[memo_key] = result
  return result

def parse(start_symbol, cnf_rules, tokens):
  memo = {}
  for i, (h,t) in enumerate(cnf_rules):
    if h == start_symbol:
      result = cyk(tokens, cnf_rules, len(tokens), 0, i, memo=memo)
      if result is not None:
        return result
  # no match for start symbol found
  return None

start_symbol, cnf_rules = to_cnf('expression', BASE_RULES)
print(start_symbol)
for i, rule in enumerate(cnf_rules):
  print('{} {}'.format(i, rule))

string = "(5*(3+2))*2"
#string = "+"
tokens = list(tokenize(string))
print('string: {}'.format(string))
print('tokens: {}'.format(tokens))

result = parse(start_symbol, cnf_rules, tokens)
if result is None:
  print("Could not parse.")
else:
  print_parse_node(result)

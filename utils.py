def print_parse_node(parse_node, offset = 0):
  if type(parse_node[1]) is list:
    print('{}{}'.format('  '*offset, parse_node[0]))
    for child in parse_node[1]:
      print_parse_node(child, offset=offset+1)
  else:
    print('{}{}: {}'.format('  '*offset, parse_node[0], parse_node[1]))

def print_grammar(rules):
  for t in enumerate(rules):
    print('{} {}'.format(*t))

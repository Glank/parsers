import re

TOKEN_REGEX = [
  ('number', r'\d+\.?\d*'),
  ('+', r'\+'),
  ('-', r'-'),
  ('*', r'\*'),
  ('/', r'/'),
  ('(', r'\('),
  (')', r'\)'),
  ('ws', r'\s'),
]

def tokenize(string, skip_ws = True):
  while string:
    found = False
    for token, regex in TOKEN_REGEX:
      m = re.match(regex, string)
      if m:
        found = True
        if token != 'ws' or not skip_ws:
          yield (token, string[:m.end()])
        string = string[m.end():]
        break
    if not found:
      raise Exception('Could not tokenize string.')

_memoized_token_names = set(n for n,_ in TOKEN_REGEX)
def is_token_name(s):
  return s in _memoized_token_names

import sys

class RegError(Exception):
    pass


def read_input():
    line1 = sys.stdin.readline()
    regex = line1.rstrip("\r\n")

    txt = sys.stdin.read()

    return regex, txt

def lex_regex(regex):
    tokens = []
    i = 0
    n = len(regex)

    while i < n:
        ch = regex[i]

        if ch == ' ' or ch == '\t':
            raise RegError("whitespace is not allowed inside a regular expression")

        if ch == '\\':
            i += 1
            if i >= n:
                raise RegError("dangling escape character '\\' at end of regex")
            tokens.append(('LIT', regex[i]))
            i += 1
            continue

        if ch == '[':
            j = i + 1
            if j < n and regex[j] == '^':
                raise RegError("negated character classes [^...] are not supported")

            class_chars = []
            found_close = False

            while j < n:
                if regex[j] == ']':
                    found_close = True
                    break

                if regex[j] == '\\':
                    j += 1
                    if j >= n:
                        raise RegError("dangling escape inside character class")
                    class_chars.append(regex[j])
                    j += 1
                    continue

                if (j + 2 < n) and (regex[j + 1] == '-') and (regex[j + 2] != ']'):
                    start_c = regex[j]
                    end_c = regex[j + 2]
                    if ord(start_c) > ord(end_c):
                        raise RegError("invalid character range %s-%s" % (start_c, end_c))
                    code = ord(start_c)
                    while code <= ord(end_c):
                        class_chars.append(chr(code))
                        code += 1
                    j += 3
                    continue

                class_chars.append(regex[j])
                j += 1

            if not found_close:
                raise RegError("missing closing ']' in character class")
            if len(class_chars) == 0:
                raise RegError("empty character class []")

            tokens.append(('OP', '('))
            first = True
            for c in class_chars:
                if not first:
                    tokens.append(('OP', '|'))
                tokens.append(('LIT', c))
                first = False
            tokens.append(('OP', ')'))

            i = j + 1
            continue

        if ch in '()|*+?':
            tokens.append(('OP', ch))
            i += 1
            continue

        if ch == ']':
            raise RegError("unmatched ']' with no matching '['")

        tokens.append(('LIT', ch))
        i += 1

    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse(self):
        if len(self.tokens) == 0:
            raise RegError("empty regular expression")
        node = self.parse_union()
        if self.pos != len(self.tokens):
            raise RegError("unexpected token near position %d (check for an unmatched ')')" % self.pos)
        return node

    def parse_union(self):
        left = self.parse_concat()
        while self.peek() == ('OP', '|'):
            self.advance()
            right = self.parse_concat()
            left = ('union', left, right)
        return left

    def parse_concat(self):
        node = self.parse_repeat()
        while True:
            nxt = self.peek()
            if nxt is None:
                break
            if nxt == ('OP', '|') or nxt == ('OP', ')'):
                break
            right = self.parse_repeat()
            node = ('concat', node, right)
        return node

    def parse_repeat(self):
        node = self.parse_atom()
        nxt = self.peek()
        if nxt is not None and nxt[0] == 'OP' and nxt[1] in ('*', '+', '?'):
            op = self.advance()[1]

            nxt2 = self.peek()
            if nxt2 is not None and nxt2[0] == 'OP' and nxt2[1] in ('*', '+', '?'):
                raise RegError("stacked quantifiers are not allowed (e.g. A**)")

            if op == '*':
                node = ('star', node)
            elif op == '+':
                node = ('concat', node, ('star', node))
            elif op == '?':
                node = ('union', node, ('eps',))
        return node

    def parse_atom(self):
        tok = self.peek()
        if tok is None:
            raise RegError("unexpected end of regular expression, expected an operand")

        if tok[0] == 'LIT':
            self.advance()
            return ('lit', tok[1])

        if tok == ('OP', '('):
            self.advance()
            node = self.parse_union()
            if self.peek() != ('OP', ')'):
                raise RegError("missing closing ')'")
            self.advance()
            return node

        raise RegError("unexpected token '%s', expected a literal or '('" % tok[1])

def get_alphabet(node, alphabet_set):
    kind = node[0]
    if kind == 'lit':
        alphabet_set.add(node[1])
    elif kind == 'eps':
        pass
    elif kind in ('concat', 'union'):
        get_alphabet(node[1], alphabet_set)
        get_alphabet(node[2], alphabet_set)
    elif kind == 'star':
        get_alphabet(node[1], alphabet_set)

regex = sys.stdin.readline().rstrip("\r\n")

tokens = lex_regex(regex)
ast = Parser(tokens).parse()

print(ast)


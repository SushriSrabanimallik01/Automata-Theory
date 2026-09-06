import sys

class RegError(Exception):
    pass


def read_input():
    line1 = sys.stdin.readline()
    regex = line1.rstrip("\r\n")

    txt = sys.stdin.read()

    return regex, txt

def is_debug_mode():
    return "--debug" in sys.argv

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


class Counter:
    def __init__(self):
        self.value = 0

    def next_id(self):
        v = self.value
        self.value += 1
        return v


def new_state(nfa, counter):
    s = counter.next_id()
    nfa[s] = []
    return s


def add_edge(nfa, frm, symbol, to):
    nfa[frm].append((symbol, to))


def build_nfa(node, nfa, counter):
    kind = node[0]

    if kind == 'lit':
        ch = node[1]
        start = new_state(nfa, counter)
        accept = new_state(nfa, counter)
        add_edge(nfa, start, ch, accept)
        return start, accept

    if kind == 'eps':
        start = new_state(nfa, counter)
        accept = new_state(nfa, counter)
        add_edge(nfa, start, None, accept)
        return start, accept

    if kind == 'concat':
        left_start, left_accept = build_nfa(node[1], nfa, counter)
        right_start, right_accept = build_nfa(node[2], nfa, counter)
        add_edge(nfa, left_accept, None, right_start)
        return left_start, right_accept

    if kind == 'union':
        a_start, a_accept = build_nfa(node[1], nfa, counter)
        b_start, b_accept = build_nfa(node[2], nfa, counter)
        start = new_state(nfa, counter)
        accept = new_state(nfa, counter)
        add_edge(nfa, start, None, a_start)
        add_edge(nfa, start, None, b_start)
        add_edge(nfa, a_accept, None, accept)
        add_edge(nfa, b_accept, None, accept)
        return start, accept

    if kind == 'star':
        inner_start, inner_accept = build_nfa(node[1], nfa, counter)
        start = new_state(nfa, counter)
        accept = new_state(nfa, counter)
        add_edge(nfa, start, None, inner_start)
        add_edge(nfa, start, None, accept)
        add_edge(nfa, inner_accept, None, inner_start)
        add_edge(nfa, inner_accept, None, accept)
        return start, accept

    raise RegError("internal error: unknown AST node type %s" % kind)


def epsilon_closure(nfa, states):
    stack = list(states)
    closure = set(states)
    while len(stack) > 0:
        s = stack.pop()
        for (symbol, target) in nfa[s]:
            if symbol is None and target not in closure:
                closure.add(target)
                stack.append(target)
    return closure


def move(nfa, states, symbol):
    result = set()
    for s in states:
        for (sym, target) in nfa[s]:
            if sym == symbol:
                result.add(target)
    return result


def build_dfa(nfa, nfa_start, nfa_accept, alphabet):
    start_set = frozenset(epsilon_closure(nfa, {nfa_start}))

    dfa_transitions = {}   
    dfa_accepts = set()

    seen = set([start_set])
    worklist = [start_set]

    while len(worklist) > 0:
        current = worklist.pop()
        dfa_transitions[current] = {}

        if nfa_accept in current:
            dfa_accepts.add(current)

        for symbol in alphabet:
            moved = move(nfa, current, symbol)
            if len(moved) == 0:
                continue  

            closed = frozenset(epsilon_closure(nfa, moved))
            dfa_transitions[current][symbol] = closed

            if closed not in seen:
                seen.add(closed)
                worklist.append(closed)

    return dfa_transitions, start_set, dfa_accepts

def assign_state_ids(dfa_transitions, dfa_start):
    ids = {dfa_start: 0}
    next_id = 1
    queue = [dfa_start]

    while len(queue) > 0:
        current = queue.pop(0)
        for symbol in dfa_transitions[current]:
            target = dfa_transitions[current][symbol]
            if target not in ids:
                ids[target] = next_id
                next_id += 1
                queue.append(target)

    return ids


def print_debug_matrix(dfa_transitions, dfa_start, dfa_accepts, alphabet):
    ids = assign_state_ids(dfa_transitions, dfa_start)
    sorted_alphabet = sorted(alphabet)

    header = "State"
    for ch in sorted_alphabet:
        header += ", " + ch
    print(header, file=sys.stderr)

    states_in_order = sorted(ids.keys(), key=lambda s: ids[s])

    for state in states_in_order:
        label = str(ids[state])
        is_start = (state == dfa_start)
        is_accept = (state in dfa_accepts)

        if is_start and is_accept:
            label = "->*" + label
        elif is_start:
            label = "->" + label
        elif is_accept:
            label = "*" + label

        row = label
        for ch in sorted_alphabet:
            if ch in dfa_transitions[state]:
                row += ", " + str(ids[dfa_transitions[state][ch]])
            else:
                row += ", -"
        print(row, file=sys.stderr)

def tokenize_words(txt):
    return txt.split()


def simulate(dfa_transitions, dfa_start, dfa_accepts, word):
    curr = dfa_start
    for ch in word:
        if ch in dfa_transitions[curr]:
            curr = dfa_transitions[curr][ch]
        else:
            return False
    return curr in dfa_accepts

def main():
    debug = is_debug_mode()
    regex_str, txt = read_input()

    try:
        tokens = lex_regex(regex_str)
        parser = Parser(tokens)
        ast = parser.parse()
    except RegError as e:
        print("Parse error: " + str(e), file=sys.stderr)
        sys.exit(1)

    alphabet = set()
    get_alphabet(ast, alphabet)

    nfa = {}
    counter = Counter()
    nfa_start, nfa_accept = build_nfa(ast, nfa, counter)

    dfa_transitions, dfa_start, dfa_accepts = build_dfa(nfa, nfa_start, nfa_accept, alphabet)

    if debug:
        print_debug_matrix(dfa_transitions, dfa_start, dfa_accepts, alphabet)

    for word in tokenize_words(txt):
        if simulate(dfa_transitions, dfa_start, dfa_accepts, word):
            print(word)


if __name__ == "__main__":
    main()
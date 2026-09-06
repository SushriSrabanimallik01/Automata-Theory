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

regex = sys.stdin.readline().rstrip("\r\n")

tokens = lex_regex(regex)

for token in tokens:
    print(token)

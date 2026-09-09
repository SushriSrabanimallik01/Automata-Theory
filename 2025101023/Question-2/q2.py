import sys

class TokenType:
    IDENTIFIER = "IDENTIFIER"
    KEYWORD = "KEYWORD"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    SYMBOL = "SYMBOL"

token_hierarchy = {
    "move": TokenType.KEYWORD,
    "turn": TokenType.KEYWORD,
    "left": TokenType.KEYWORD,
    "right": TokenType.KEYWORD,
    "set": TokenType.KEYWORD,
    "print": TokenType.KEYWORD,
    "if": TokenType.KEYWORD,
    "else": TokenType.KEYWORD
}

VALID_SYMBOLS = {";", "=", "<", ">"}

def is_valid_identifier(lexeme):
    if not lexeme:
        return False
    if not (lexeme[0].isalpha() or lexeme[0] == '_'):
        return False
    for char in lexeme[1:]:
        if not (char.isalnum() or char == '_'):
            return False
    return True

def tokenize(source_code):
    tokens = []
    position = 0

    while position < len(source_code):
        def is_alphanumeric(char):
            return char.isalpha() or char.isdigit() or (char == '_')

        char = source_code[position]

        if char.isspace():
            position += 1
            continue

        if char.isalpha() or char == '_':
            lexeme = char
            position += 1
            while position < len(source_code) and is_alphanumeric(source_code[position]):
                lexeme += source_code[position]
                position += 1

            if lexeme in token_hierarchy:
                token_type = token_hierarchy[lexeme]
            else:
                if is_valid_identifier(lexeme):
                    token_type = TokenType.IDENTIFIER
                else:
                    raise ValueError(f"Invalid identifier: {lexeme}")
        elif char.isdigit():
            lexeme = char
            position += 1
            is_float = False

            while position < len(source_code):
                next_char = source_code[position]

                if next_char == '.':
                    if is_float:
                        raise ValueError(f"Invalid float format near {lexeme}.")

                    if (position + 1 < len(source_code)):
                        next_next_char = source_code[position+1]
                        if next_next_char.isdigit():
                            is_float = True
                        else:
                            break

                elif is_alphanumeric(next_char) and not next_char.isdigit():
                    while position < len(source_code) and is_alphanumeric(source_code[position]):
                        lexeme += source_code[position]
                        position += 1
                    if not is_valid_identifier(lexeme):
                        raise ValueError(f"Invalid identifier: {str(lexeme)}\nIdentifier can't start with digits")
                elif not next_char.isdigit():
                    break

                lexeme += next_char
                position += 1

            token_type = TokenType.FLOAT if is_float else TokenType.INTEGER

        else: 
            if char == '=' and position + 1 < len(source_code) and source_code[position + 1] == '=':
                lexeme = "=="
                position += 2
            elif char in VALID_SYMBOLS:
                lexeme = char
                position += 1
            else:
                raise ValueError(f"Unrecognized character: {char}")

            token_type = TokenType.SYMBOL

        tokens.append((token_type, lexeme))

    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def curr(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def is_keyword(self, tok, value):
        return tok is not None and tok[0] == TokenType.KEYWORD and tok[1] == value

    def is_symbol(self, tok, value):
        return tok is not None and tok[0] == TokenType.SYMBOL and tok[1] == value

    def expect_keyword(self, value):
        tok = self.curr()
        if not self.is_keyword(tok, value):
            raise SyntaxError("expected keyword '%s'" % value)
        return self.advance()

    def expect_symbol(self, value):
        tok = self.curr()
        if not self.is_symbol(tok, value):
            raise SyntaxError("expected '%s'" % value)
        return self.advance()

    def parse_x(self, context=""):
        tok = self.curr()
        if tok is not None and tok[0] in (TokenType.INTEGER, TokenType.FLOAT, TokenType.IDENTIFIER):
            return self.advance()
        message = "Expected integer, float, or identifier"
        if context:
            message += " " + context
        raise SyntaxError(message)

    def parse_relop(self):
        tok = self.curr()
        if tok is not None and tok[0] == TokenType.SYMBOL and tok[1] in ('<', '>', '=='):
            return self.advance()
        raise SyntaxError("expected a relational operator (<, >, ==)")

    def parse_move(self):
        self.expect_keyword('move')
        self.parse_x("after 'move'")
        self.expect_symbol(';')

    def parse_turn(self):
        self.expect_keyword('turn')
        tok = self.curr()
        if self.is_keyword(tok, 'left') or self.is_keyword(tok, 'right'):
            self.advance()
        else:
            raise SyntaxError("expected 'left' or 'right' after 'turn'")
        self.expect_symbol(';')

    def parse_set(self):
        self.expect_keyword('set')
        tok = self.curr()
        if tok is not None and tok[0] == TokenType.IDENTIFIER:
            self.advance()
        else:
            raise SyntaxError("expected an identifier after 'set'")
        self.expect_symbol('=')
        self.parse_x("after '='")
        self.expect_symbol(';')

    def parse_print(self):
        self.expect_keyword('print')
        self.parse_x("after 'print'")
        self.expect_symbol(';')

    def parse_if(self):
        self.expect_keyword('if')
        self.parse_x("after 'if'")
        self.parse_relop()
        self.parse_x("after relational operator")
        self.parse_move()
        self.parse_else_part()

    def parse_else_part(self):
        tok = self.curr()
        if self.is_keyword(tok, 'else'):
            self.advance()
            self.parse_move()

    def parse_statement(self):
        tok = self.curr()

        if self.is_keyword(tok, 'else'):
            raise SyntaxError("'else' occurs before 'if'")

        if self.is_keyword(tok, 'move'):
            self.parse_move()
        elif self.is_keyword(tok, 'turn'):
            self.parse_turn()
        elif self.is_keyword(tok, 'set'):
            self.parse_set()
        elif self.is_keyword(tok, 'print'):
            self.parse_print()
        elif self.is_keyword(tok, 'if'):
            self.parse_if()
        else:
            raise SyntaxError("unexpected token, expected a statement (move/turn/set/print/if)")

    def parse_prog(self):
        while self.curr() is not None:
            self.parse_statement()


def checkGrammar(tokens):
    
    parser = Parser(tokens)
    parser.parse_prog()

if __name__ == "__main__":
    source_code = sys.stdin.read().strip()

    if not source_code:
        sys.exit(0)

    try:
        tokens = tokenize(source_code)

        for token in tokens:
            print(f"Token Type: {token[0]}, Token Value: {token[1]}")

        checkGrammar(tokens)

    except ValueError as e:
        print(f"ValueError: {e}")
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
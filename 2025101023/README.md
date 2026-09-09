# Automata Theory Programming Assignment

**Course:** Automata Theory
**Assignment:** Programming Assignment
**Roll Number:** 2025101023

This assignment contains two parts:

* **Question 1:** RegExpert - Regex Engine
* **Question 2:** Syntactic Analysis


---

# Question 1: RegExpert

## 1. Overview

The first question is about implementing a small regular expression engine without using Python's built-in `re` module.

The main idea is to take a regular expression given by the user and convert it step by step into an automaton which can then be used to check whether each input word matches the regular expression.

I divided the implementation into the following stages:

1. Read the input
2. Tokenize the regular expression
3. Parse the regular expression
4. Construct an NFA using Thompson's construction
5. Convert the NFA into a DFA using subset construction
6. Assign state numbers to the DFA states
7. Simulate every input word on the DFA
8. Print the words which are accepted
9. Added a debug mode to display the DFA transition table

The complete flow is:

```text
Regular Expression
        |
        v
   Regex Lexer
        |
        v
 Regex Parser
        |
        v
 Thompson NFA
        |
        v
 Subset Construction
        |
        v
      DFA
        |
        v
 DFA Simulation
        |
        v
Matching Words
```

---

## 2. Reading the Input

I first read the complete input from standard input.

The first line is treated as the regular expression and the remaining lines contain the text whose words have to be checked.

The input is read until EOF because the assignment allows multiple lines of input text.

I also check whether debug mode has been requested. The debug option is used separately so that the normal output only contains matching words.

---

## 3. Regular Expression Lexing

Before constructing an automaton, I need to understand the different parts of the regular expression.

For this, I created a `lex_regex()` function.

This function scans the regular expression character by character and converts it into tokens.

The lexer handles:

* Literal characters
* `|`
* `*`
* `+`
* `?`
* `(`
* `)`
* `[`
* `]`
* `-`
* Escaped characters


---

## 4. Parsing the Regular Expression

After lexing, I used a parser to understand the structure of the regular expression.

I created a `Parser` class for this.

The parser follows the precedence of regular expression operators.

The main parsing functions are:

* `parse()`
* `parse_union()`
* `parse_concat()`
* `parse_repeat()`
* `parse_atom()`

### `parse()`

This is the main entry point of the parser.

It starts parsing the complete regular expression and makes sure that the entire expression has been consumed.

If something invalid is left after parsing, the program reports a regex error.

### `parse_union()`

This handles the `|` operator.

For example:

```text
a|b
```

means either `a` or `b`.

Union has lower precedence than concatenation, so this function is placed higher in the parsing hierarchy.

### `parse_concat()`

This handles concatenation.

For example:

```text
abc
```

means:

```text
a followed by b followed by c
```

The parser therefore creates a sequence of regex expressions for concatenated characters.

### `parse_repeat()`

This handles the repetition operators:

```text
*
+
?
```

Their meanings are:

* `*` → zero or more occurrences
* `+` → one or more occurrences
* `?` → zero or one occurrence


### `parse_atom()`

This handles the smallest units of the regular expression.

An atom can be:

* A literal
* A character class
* A grouped expression
* An escaped character

Parentheses are handled here so expressions such as:

```text
(a|b)c
```

are treated correctly.

---

# 5. Character Classes and Ranges

I also implemented character classes such as:

```text
[abc]
```

which means any one of:

```text
a
b
c
```

Ranges such as:

```text
[a-z]
```

are also expanded into the corresponding set of characters.

The characters obtained from the regex are later used to form the alphabet of the automaton.

Negated character classes are not implemented because they are not required by the assignment.

---

# 6. Finding the Alphabet

After parsing the regular expression, I collect all the characters which can occur as actual input symbols.

I created the `get_alphabet()` function for this.

The alphabet is important because the DFA transition table needs one column for each input symbol.

I keep the alphabet sorted so that the DFA debug output has a consistent order.

---

# 7. Thompson NFA Construction

Once the regex has been parsed, I convert it into an NFA using Thompson's construction.

The NFA is useful because regular expression operations can be represented using small automaton fragments.

I used functions such as:

* `new_state()`
* `add_edge()`
* `build_nfa()`

---

## 8. Creating NFA States

I used `new_state()` to create new NFA states.

Each state gets a unique integer identifier.

An NFA transition can either contain:

* an actual input character, or
* an epsilon transition

An epsilon transition means that the automaton can move without consuming an input character.

---

## 9. Adding NFA Transitions

The `add_edge()` function is used to connect two NFA states.

For example, a normal transition can look conceptually like:

```text
state 1 --a--> state 2
```

while an epsilon transition can look like:

```text
state 1 --ε--> state 2
```

I used epsilon transitions while implementing operations such as union, star and optional repetition.

---

# 10. Building NFA Fragments

The `build_nfa()` function recursively constructs NFA fragments from the parsed regex structure.

Different regex operations are handled separately.

### Literal

For a literal such as:

```text
a
```

I create a start state and an end state with an `a` transition between them.

```text
start --a--> end
```

### Concatenation

For:

```text
ab
```

the end state of the NFA for `a` is connected to the start state of the NFA for `b`.

Conceptually:

```text
a NFA -> b NFA
```

### Union

For:

```text
a|b
```

I create a new start and end state.

The new start has epsilon transitions to both alternatives.

```text
          --a--
         /     \
start --ε       ε--> end
         \     /
          --b--
```

### Kleene Star

For:

```text
a*
```

I create epsilon transitions which allow:

* skipping the expression completely
* entering the expression
* repeating it
* leaving it

This gives the required zero-or-more behavior.

### Plus

For:

```text
a+
```

the expression must occur at least once.

I therefore construct it so that the expression is entered once before the repetition is allowed.


---

# 11. Epsilon Closure

After creating the NFA, I need to convert it into a DFA.

For this I implemented `epsilon_closure()`.

The epsilon closure of a state is the set of states that can be reached from that state using only epsilon transitions.

For a set of states, I repeatedly follow epsilon transitions until no new states can be reached.

This is necessary because an NFA can make epsilon moves without consuming a character, whereas a DFA needs to know the complete set of possible NFA states after reading each input symbol.

---

# 12. NFA Move Operation

I also implemented a `move()` function.

Given:

* a set of NFA states
* an input character

the function finds all states reachable using that character.

After finding those states, epsilon closure is applied to them.

The combination is what allows the NFA to be represented as a DFA state.

---

# 13. Subset Construction

I then converted the NFA into a DFA using subset construction.

The important idea is that:

> One DFA state represents a set of NFA states.

For example, a DFA state might represent:

```text
{0, 1, 4}
```

meaning that after reading some input, the NFA could currently be in any of states 0, 1 or 4.

The `build_dfa()` function performs this conversion.

I start with the epsilon closure of the NFA start state.

Then, for every DFA state and every symbol in the alphabet, I calculate the next set of NFA states.

If this set has not been seen before, it becomes a new DFA state.

This process continues until there are no new DFA states.

---

# 14. Identifying Final DFA States

A DFA state is accepting if the set of NFA states represented by that DFA state contains the NFA's final state.

Therefore, while constructing the DFA, I check whether the NFA accepting state belongs to each subset.

If it does, I mark that DFA state as a final state.

---

# 15. Assigning DFA State Numbers

The subsets generated during subset construction are sets of NFA states, so I assign simple integer IDs to them.

I used `assign_state_ids()` for this purpose.

This makes the DFA easier to store, simulate and display in the debug table.

---

# 16. Debug DFA Matrix

I also implemented the `--debug` option required by the assignment.

When debug mode is enabled, the final DFA transition matrix is printed to standard error instead of standard output.

The matrix contains:

* DFA state numbers
* Alphabet symbols as columns
* Start-state marker `->`
* Final-state marker `*`
* `->*` when a state is both start and final
* `-` for missing/dead transitions

The alphabet columns are sorted in ASCII order.

---

# 17. Tokenizing the Input Text

After constructing the DFA, I process the remaining input text.

I created `tokenize_words()` for this.

The input is split into words based on whitespace.

Punctuation is not removed from the words because the assignment requires punctuation to remain attached.

---

# 18. DFA Simulation

Finally, I simulate each word using the DFA.

I created the `simulate()` function for this.

For every character in the word:

1. Start from the DFA start state.
2. Read the current character.
3. Follow the corresponding DFA transition.
4. Move to the next DFA state.
5. Continue until all characters are consumed.

After the complete word has been processed, I check whether the current DFA state is an accepting state.

If it is accepting, the word is printed.

Otherwise, it is ignored.

This means the matching is a **full-word match**, not a substring search.

---

# 19. Error Handling in Question 1

I used `RegError` for invalid regular expressions.

Errors can occur during:

* Regex tokenization
* Parsing
* Grouping
* Character classes
* Invalid operators
* Missing closing brackets or parentheses
* Invalid repetition placement

The program reports the regex error instead of continuing with an invalid automaton.

---

# Question 2: Syntactic Analysis

## 1. Overview

The second question is about lexical analysis followed by syntactic analysis.

The tokenizer identifies the different types of tokens in the input, and then a recursive-descent parser checks whether those tokens follow the grammar given in the assignment.

The overall process is:

```text
Source Code
     |
     v
   Lexer
     |
     v
   Tokens
     |
     v
Recursive-Descent Parser
     |
     v
Grammar Check
```

The grammar used is:

```text
S → P

P → statement P | ε

statement → Move | Turn | Set | Print | If

Move → move x ;

Turn → turn left ;
     | turn right ;

Set → set id = x ;

Print → print x ;

If → if x RelOp x Move ElsePart

ElsePart → else Move | ε

RelOp → < | > | ==
```

where:

```text
x → integer | float | id
```

---

# 2. Token Types

I defined a `TokenType` class containing the token categories used by the lexer.

The token types are:

* `IDENTIFIER`
* `KEYWORD`
* `INTEGER`
* `FLOAT`
* `SYMBOL`

This makes it easier for the parser to distinguish between different types of input.

---

# 3. Keywords

I created `token_hierarchy` to store the keywords of the language.

The keywords are:

```text
move
turn
left
right
set
print
if
else
```

Whenever one of these words is encountered, it is stored as a `KEYWORD` token.

Other valid names are treated as identifiers.

---

# 4. Valid Symbols

The symbols used by the language are stored in `VALID_SYMBOLS`.

These include:

```text
;
=
<
>
```

The equality operator:

```text
==
```

is handled separately while tokenizing.

---

# 5. Identifier Validation

I created `is_valid_identifier()` to check whether a lexeme can be used as an identifier.

An identifier must start with either:

* a letter, or
* `_`

After that, it can contain:

* letters
* digits
* `_`

An identifier cannot start with a digit.

---

# 6. Tokenization

The `tokenize()` function scans the source code from left to right.

I maintain a `position` variable to keep track of where I am in the input.

Whitespace is ignored.

Depending on the current character, the lexer decides whether it is reading:

* an identifier/keyword
* an integer/float
* a symbol

---

## 7. Reading Identifiers and Keywords

If the current character is a letter or `_`, I keep reading characters while they are alphanumeric or `_`.

After obtaining the complete lexeme, I check whether it is present in `token_hierarchy`.

If it is present, I classify it as a keyword.

Otherwise, I validate it as an identifier.

---

# 8. Reading Integers and Floats

If the current character is a digit, I start reading a number.

The lexer checks whether the number contains a decimal point.

For example:

```text
10
```

is classified as:

```text
INTEGER
```

while:

```text
10.5
```

is classified as:

```text
FLOAT
```

I also check for invalid float formats, such as having more than one decimal point.

---

# 9. Handling `==`

The equality operator contains two characters:

```text
==
```

Therefore, when the lexer encounters `=`, it first checks whether the next character is also `=`.

If so, the two characters are combined into one `SYMBOL` token with value:

```text
==
```

Otherwise, a single `=` is treated as the assignment symbol.

---

# 10. Lexical Errors

If the lexer encounters a character that does not belong to the language, it raises a `ValueError`.

For example, unsupported characters are rejected rather than being silently ignored.

The program catches the error and prints it using the required format:

```text
ValueError: ...
```

---

# 11. Recursive-Descent Parser

After tokenization, I created a `Parser` class.

The parser stores:

* the list of tokens
* the current position

The parser then moves through the tokens while checking the grammar.

Each important grammar rule has a corresponding parsing function.

---

# 12. `curr()` and `advance()`

The parser uses two basic functions to move through the token list.

### `curr()`

This returns the current token without consuming it.

If there are no tokens left, it returns `None`.

### `advance()`

This consumes the current token and moves the position forward by one.

These two functions are used by almost every other parser function.

---

# 13. Checking Keywords and Symbols

I created:

```text
is_keyword()
is_symbol()
```

These functions make the parser checks simpler.

---

# 14. `expect_keyword()` and `expect_symbol()`

These functions are used when the grammar requires a specific token.

---

# 15. Parsing `x`

The grammar defines:

```text
x → integer | float | id
```

I implemented this in `parse_x()`.

The function checks whether the current token is one of:

```text
INTEGER
FLOAT
IDENTIFIER
```

If yes, it consumes the token.

Otherwise, it raises a syntax error.

This function is reused in several grammar rules such as `Move`, `Set`, `Print`, and `If`.

---

# 16. Parsing Relational Operators

The grammar allows:

```text
<
>
==
```

I implemented this in `parse_relop()`.

The parser checks that the current token is a symbol and that its value is one of these three operators.

Anything else produces a `SyntaxError`.

---

# 17. Parsing Move

The grammar is:

```text
Move → move x ;
```

I implemented this in `parse_move()`.

The parser performs the following actions:

1. Check for `move`
2. Parse `x`
3. Check for `;`

For example:

```text
move 10;
```

is valid according to the grammar.

---

# 18. Parsing Turn

The grammar is:

```text
Turn → turn left ;
     | turn right ;
```

I implemented this in `parse_turn()`.

The parser:

1. Checks for `turn`
2. Checks whether the next keyword is `left` or `right`
3. Checks for `;`

Therefore both:

```text
turn left;
```

and:

```text
turn right;
```

follow the grammar.

---

# 19. Parsing Set

The grammar is:

```text
Set → set id = x ;
```

I implemented this in `parse_set()`.

The parser:

1. Checks for `set`
2. Requires an identifier
3. Checks for `=`
4. Parses `x`
5. Checks for `;`

So an example of the expected structure is:

```text
set value = 10;
```

---

# 20. Parsing Print

The grammar is:

```text
Print → print x ;
```

I implemented this using `parse_print()`.

The parser:

1. Checks for `print`
2. Parses `x`
3. Checks for `;`

---

# 21. Parsing If

The grammar for an `if` statement is:

```text
If → if x RelOp x Move ElsePart
```

I implemented this in `parse_if()`.

The parser performs these steps:

1. Check for `if`
2. Parse the first `x`
3. Parse the relational operator
4. Parse the second `x`
5. Parse the required `Move`
6. Parse the optional `ElsePart`

This directly follows the order of the grammar.

---

# 22. Parsing ElsePart

The grammar is:

```text
ElsePart → else Move | ε
```

This means that an `else` is optional.

I implemented this in `parse_else_part()`.

The parser checks the current token.

If it is:

```text
else
```

then it consumes the `else` and parses the following `Move`.

If there is no `else`, the function simply returns because the epsilon production allows the part to be empty.

---

# 23. Parsing Statements

I implemented `parse_statement()` to decide which statement grammar rule needs to be used.

Depending on the current keyword:

```text
move  → parse_move()
turn  → parse_turn()
set   → parse_set()
print → parse_print()
if    → parse_if()
```

If none of these are present, the parser raises a syntax error because a valid statement was expected.

I also explicitly reject an `else` appearing by itself before an `if` statement.

---

# 24. Parsing the Complete Program

The `parse_prog()` function implements:

```text
P → statement P | ε
```

It keeps parsing statements while tokens are still available.

When all tokens have been consumed, parsing finishes successfully.

This also represents the epsilon case because the parser simply stops when there are no more tokens.

---

# 25. `checkGrammar()`

The assignment requires a function named:

```text
checkGrammar(tokens)
```

I implemented it by creating a `Parser` object and calling:

```text
parser.parse_prog()
```

Therefore the token list produced by the lexer is passed directly to the recursive-descent parser.

---

# 26. Output and Error Handling

The main program first reads the source code and tokenizes it.

If tokenization is successful, all recognized tokens are printed in the required format:

```text
Token Type: ..., Token Value: ...
```

After printing the tokens, `checkGrammar()` is called.

If a syntax error occurs, the program prints:

```text
SyntaxError: ...
```

The successfully recognized tokens are still printed before the syntax error because tokenization is completed before grammar checking.

Lexical errors are handled separately using:

```text
ValueError
```

---

# 27. Dangling Else

The grammar used in this assignment has a simple `If` structure:

```text
If → if x RelOp x Move ElsePart
```

and the `Move` production is not another `If`.

Therefore, the usual dangling-else ambiguity does not arise in this grammar.

I did not need a separate dangling-else resolution mechanism.

The parser simply checks for an optional `else` immediately after the required `Move` in `parse_if()`.

---

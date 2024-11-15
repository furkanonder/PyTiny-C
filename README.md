# PyTiny-C

A Tiny-C language compiler, rewritten in Python(It has been converted from C to Python with as much one-to-one
correlation as possible). 

Tiny-C is a considerably stripped down version of C and it is meant as a pedagogical tool for learning about compilers.
The integer global variables "a" to "z" are predefined and initialized to zero, and it is not possible to declare new
variables.  The compiler reads the program from standard input and prints out the value of the variables that are not
zero.

The grammar of Tiny-C in EBNF is:
```ebnf
<program> ::= <statement>
<statement> ::= "if" <paren_expr> <statement> |
                "if" <paren_expr> <statement> "else" <statement> |
                "while" <paren_expr> <statement> |
                "do" <statement> "while" <paren_expr> ";" |
                "{" { <statement> } "}" |
                <expr> ";" |
                ";"
<paren_expr> ::= "(" <expr> ")"
<expr> ::= <test> | <id> "=" <expr>
<test> ::= <sum> | <sum> "<" <sum>
<sum> ::= <term> | <sum> "+" <term> | <sum> "-" <term>
<term> ::= <id> | <int> | <paren_expr>
<id> ::= "a" | "b" | "c" | "d" | ... | "z"
<int> ::= <an_unsigned_decimal_integer>
```

Here are a few invocations of the compiler:
```sh
$ echo "a=b=c=2<3;" | python tinyc.py
a = 1
b = 1
c = 1
$ echo "{ i=1; while (i<100) i=i+i; }" | python tinyc.py
i = 128
$ echo "{ i=125; j=100; while (i-j) if (i<j) j=j-i; else i=i-j; }" | python tinyc.py
i = 25
j = 25
$ echo "{ i=1; do i=i+10; while (i<50); }" | python tinyc.py
i = 51
$ echo "{ i=1; while ((i=i+10)<50) ; }" | python tinyc.py
i = 51
$ echo "{ i=7; if (i<5) x=1; if (i<10) y=2; }" | python tinyc.py
i = 7
y = 2
```
The compiler does a minimal amount of error checking to help highlight the structure of the compiler.

## Reference
- http://www.iro.umontreal.ca/~felipe/IFT2030-Automne2002/Complements/tinyc.c

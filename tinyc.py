import array
import sys
from enum import Enum, EnumMeta
from typing import Optional

class CustomEnumMeta(EnumMeta):
    def __getitem__(self, index):
        return list(self)[index].name

"""
This is a compiler for the Tiny-C language. Tiny-C is a considerably stripped down version of C and it is meant as a
pedagogical tool for learning about compilers. The integer global variables "a" to "z" are predefined and initialized
to zero, and it is not possible to declare new variables.  The compiler reads the program from standard input and prints
out the value of the variables that are not zero. The grammar of Tiny-C in EBNF is:

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

Here are a few invocations of the compiler:

$ echo "a=b=c=2<3;" | python tiny_c.py
a = 1
b = 1
c = 1
$ echo "{ i=1; while (i<100) i=i+i; }" | python tiny_c.py
i = 128
$ echo "{ i=125; j=100; while (i-j) if (i<j) j=j-i; else i=i-j; }" | python tiny_c.py
i = 25
j = 25
$ echo "{ i=1; do i=i+10; while (i<50); }" | python tiny_c.py
i = 51
$ echo "{ i=1; while ((i=i+10)<50) ; }" | python tiny_c.py
i = 51
$ echo "{ i=7; if (i<5) x=1; if (i<10) y=2; }" | python tiny_c.py
i = 7
y = 2

The compiler does a minimal amount of error checking to help highlight the structure of the compiler.
"""

# ---------------------------------------------------------------------------#

# Lexer. #

class Symbol(Enum):
    DO_SYM = 0
    ELSE_SYM = 1
    IF_SYM = 2
    WHILE_SYM = 3
    LBRA = 4
    RBRA = 5
    LPAR = 6
    RPAR = 7
    PLUS = 8
    MINUS = 9
    LESS = 10
    SEMI = 11
    EQUAL = 12
    INT = 13
    ID = 14
    EOI = 15

words: list[Optional[str]] = ["do", "else", "if", "while", None]

ch: str = " "
sym: int
int_val: int
id_name: str = ""

def syntax_error() -> None:
    print("syntax error", file=sys.stderr)
    sys.exit(1)

def next_ch() -> None:
    global ch
    ch = sys.stdin.read(1)
    if ch == "":
        ch = "EOF"

def next_sym() -> None:
    global sym, int_val, id_name, ch
    match ch:
        case " " | "\n":
            next_ch()
            return next_sym()
        case "EOF":
            sym = Symbol.EOI.value
            return
        case "{":
            next_ch()
            sym = Symbol.LBRA.value
            return
        case "}":
            next_ch()
            sym = Symbol.RBRA.value
            return
        case "(":
            next_ch()
            sym = Symbol.LPAR.value
            return
        case ")":
            next_ch()
            sym = Symbol.RPAR.value
            return
        case "+":
            next_ch()
            sym = Symbol.PLUS.value
            return
        case "-":
            next_ch()
            sym = Symbol.MINUS.value
            return
        case "<":
            next_ch()
            sym = Symbol.LESS.value
            return
        case ";":
            next_ch()
            sym = Symbol.SEMI.value
            return
        case "=":
            next_ch()
            sym = Symbol.EQUAL.value
            return
        case _:
            if ch >= "0" and ch <= "9":
                int_val = 0
                while ch >= "0" and ch <= "9":
                    int_val = int_val * 10 + ord(ch) - ord("0")
                    next_ch()
                sym = Symbol.INT.value
            elif ch >= "a" and ch <= "z":
                id_name = ""
                while (ch >= "a" and ch <= "z") or (ch == "_"):
                    id_name += ch
                    next_ch()
                sym = 0
                while words[sym] != None and words[sym] != id_name:
                    sym += 1
                if words[sym] == None:
                    if len(id_name) == 1:
                        sym = Symbol.ID.value
                    else:
                        syntax_error()
            else:
                syntax_error()

# ---------------------------------------------------------------------------#

# Parser. #

class NodeType(Enum, metaclass=CustomEnumMeta):
    VAR = 0
    CST = 1
    ADD = 2
    SUB = 3
    LT = 4
    SET = 5
    IF1 = 6
    IF2 = 7
    WHILE = 8
    DO = 9
    EMPTY = 10
    SEQ = 11
    EXPR = 12
    PROG = 13

class Node:
    def __init__(self, kind: int):
        self.kind: int = kind
        self.o1: Node
        self.o2: Node
        self.o3: Node
        self.val: int

def new_node(k: int) -> Node:
    return Node(k)

def paren_expr() -> Node: # <paren_expr> ::= "(" <expr> ")"
    if sym == Symbol.LPAR.value:
        next_sym()
    else:
        syntax_error()
    x = expr()
    if sym == Symbol.RPAR.value:
        next_sym()
    else:
        syntax_error()
    return x

def term() -> Node: # <term> ::= <id> | <int> | <paren_expr>
    global id_name
    if sym == Symbol.ID.value:
        x = new_node(NodeType.VAR.value)
        x.val = ord(id_name[0]) - ord("a")
        next_sym()
    elif sym == Symbol.INT.value:
        x = new_node(NodeType.CST.value)
        x.val = int_val
        next_sym()
    else:
        x = paren_expr()
    return x

def _sum() -> Node: # <sum> ::= <term> | <sum> "+" <term> | <sum> "-" <term>
    x = term()
    while sym in [Symbol.PLUS.value, Symbol.MINUS.value]:
        t = x
        x = new_node(NodeType.ADD.value if sym == Symbol.PLUS.value else NodeType.SUB.value)
        next_sym()
        x.o1 = t
        x.o2 = term()
    return x

def test() -> Node: # <test> ::= <sum> | <sum> "<" <sum>
    x = _sum()
    if sym == Symbol.LESS.value:
        t = x
        x = new_node(NodeType.LT.value)
        next_sym()
        x.o1 = t
        x.o2 = _sum()
    return x

def expr() -> Node: # <expr> ::= <test> | <id> "=" <expr>
    if sym != Symbol.ID.value:
        return test()
    x = test()
    if x.kind == NodeType.VAR.value and sym == Symbol.EQUAL.value:
        t = x
        x = new_node(NodeType.SET.value)
        next_sym()
        x.o1 = t
        x.o2 = expr()
    return x

def statement() -> Node:
    if sym == Symbol.IF_SYM.value: # "if" <paren_expr> <statement>
        x = new_node(NodeType.IF1.value)
        next_sym()
        x.o1 = paren_expr()
        x.o2 = statement()
        if sym == Symbol.ELSE_SYM.value: # ... "else" <statement>
            x.kind = NodeType.IF2.value
            next_sym()
            x.o3 = statement()
    elif sym == Symbol.WHILE_SYM.value: # "while" <paren_expr> <statement>
        x = new_node(NodeType.WHILE.value)
        next_sym()
        x.o1 = paren_expr()
        x.o2 = statement()
    elif sym == Symbol.DO_SYM.value: # "do" <statement> "while" <paren_expr> ";"
        x = new_node(NodeType.DO.value)
        next_sym()
        x.o1 = statement()
        if sym == Symbol.WHILE_SYM.value:
            next_sym()
        else:
            syntax_error()
        x.o2 = paren_expr()
        if sym == Symbol.SEMI.value:
            next_sym()
        else:
            syntax_error()
    elif sym == Symbol.SEMI.value: # ";"
        x = new_node(NodeType.EMPTY.value)
        next_sym()
    elif sym == Symbol.LBRA.value: # "{" { <statement> } "}"
        x = new_node(NodeType.EMPTY.value)
        next_sym()
        while sym != Symbol.RBRA.value:
            t = x
            x = new_node(NodeType.SEQ.value)
            x.o1 = t
            x.o2 = statement()
        next_sym()
    else: # <expr> ";"
        x = new_node(NodeType.EXPR.value)
        x.o1 = expr()
        if sym == Symbol.SEMI.value:
            next_sym()
        else:
            syntax_error()
    return x

def program() -> Node: # <program> ::= <statement>
    global sym
    x = new_node(NodeType.PROG.value)
    next_sym()
    x.o1 = statement()
    if sym != Symbol.EOI.value:
        syntax_error()
    return x

# ---------------------------------------------------------------------------#

# Code generator #

class Instruction(Enum, metaclass=CustomEnumMeta):
    IFETCH = 0
    ISTORE = 1
    IPUSH = 2
    IPOP = 3
    IADD = 4
    ISUB = 5
    ILT = 6
    JZ = 7
    JNZ = 8
    JMP = 9
    HALT = 10

_object: array.array = array.array("b", [0] * 1000)
here: int = 0

def g(c: int) -> None:
    global here
    _object[here] = c
    here += 1

def hole() -> int:
    global here
    here += 1
    return here - 1

def fix(src: int, dst: int) -> None:
    _object[src] = dst - src

def c(x: Node) -> None:
    match NodeType[x.kind]:
        case NodeType.VAR.name:
            g(Instruction.IFETCH.value)
            g(x.val)
        case NodeType.CST.name:
            g(Instruction.IPUSH.value)
            g(x.val)
        case NodeType.ADD.name:
            c(x.o1)
            c(x.o2)
            g(Instruction.IADD.value)
        case NodeType.SUB.name:
            c(x.o1)
            c(x.o2)
            g(Instruction.ISUB.value)
        case NodeType.LT.name:
            c(x.o1)
            c(x.o2)
            g(Instruction.ILT.value)
        case NodeType.SET.name:
            c(x.o2)
            g(Instruction.ISTORE.value)
            g(x.o1.val)
        case NodeType.IF1.name:
            c(x.o1)
            g(Instruction.JZ.value)
            p1 = hole()
            c(x.o2)
            fix(p1, here)
        case NodeType.IF2.name:
            c(x.o1)
            g(Instruction.JZ.value)
            p1 = hole()
            c(x.o2)
            g(Instruction.JMP.value)
            p2 = hole()
            fix(p1, here)
            c(x.o3)
            fix(p2, here)
        case NodeType.WHILE.name:
            p1 = here
            c(x.o1)
            g(Instruction.JZ.value)
            p2 = hole()
            c(x.o2)
            g(Instruction.JMP.value)
            fix(hole(), p1)
            fix(p2, here)
        case NodeType.DO.name:
            p1 = here
            c(x.o1)
            c(x.o2)
            g(Instruction.JNZ.value)
            fix(hole(), p1)
        case NodeType.EMPTY.name:
            pass
        case NodeType.SEQ.name:
            c(x.o1)
            c(x.o2)
        case NodeType.EXPR.name:
            c(x.o1)
            g(Instruction.IPOP.value)
        case NodeType.PROG.name:
            c(x.o1)
            g(Instruction.HALT.value)

# --------------------------------------------------------------------------- #

# Virtual machine #

_globals = array.array("i", [0] * 26)

def run() -> None:
    global _globals, _object
    stack, sp = array.array("i", [0] * 1000), 0
    pc = 0
    while True:
        instruction = Instruction[_object[pc]]
        pc += 1
        match instruction:
            case Instruction.IFETCH.name:
                stack[sp] = _globals[_object[pc]]
                sp += 1
                pc += 1
            case Instruction.ISTORE.name:
                _globals[_object[pc]] = stack[sp - 1]
                pc += 1
            case Instruction.IPUSH.name:
                stack[sp] = _object[pc]
                sp += 1
                pc += 1
            case Instruction.IPOP.name:
                sp -= 1
            case Instruction.IADD.name:
                stack[sp - 2] += stack[sp - 1]
                sp -= 1
            case Instruction.ISUB.name:
                stack[sp - 2] -= stack[sp - 1]
                sp -= 1
            case Instruction.ILT.name:
                stack[sp - 2] = int(stack[sp - 2] < stack[sp - 1])
                sp -= 1
            case Instruction.JZ.name:
                sp -= 1
                if stack[sp] == 0:
                    pc += _object[pc]
                else:
                    pc += 1
            case Instruction.JNZ.name:
                sp -= 1
                if stack[sp] != 0:
                    pc += _object[pc]
                else:
                    pc += 1
            case Instruction.JMP.name:
                pc += _object[pc]
            case Instruction.HALT.name:
                break

# ---------------------------------------------------------------------------#

# Main program. #

if __name__ == "__main__":
    c(program())

    for i in range(26):
        _globals[i] = 0
    run()
    for i in range(26):
        if _globals[i] != 0:
            print(f"{(ord('a') + i)} = {_globals[i]}")

    sys.exit(0)

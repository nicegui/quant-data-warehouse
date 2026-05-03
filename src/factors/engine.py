"""因子表达式解析器 + 求值引擎

将字符串表达式解析为 AST，然后在 Polars DataFrame 上求值。

支持的表达式语法：
  - 变量引用: $close, $open, $high, $low, $volume, $amount
  - 函数调用: Ref(X, N), Mean(X, N), Std(X, N), RSI(X, N), MACD(X), ...
  - 算术运算: +, -, *, /, ^ (幂)
  - 括号分组: (a + b) / c

示例:
  "Mean($close, 20) / Mean($close, 60) - 1"  → 20日均线相对60日均线偏离
  "RSI($close, 14)"                          → 14日RSI
  "Ref($close, -5) / $close - 1"             → 5日收益率
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Union

import polars as pl

from src.factors.operators import OPERATOR_MAP

# ── AST 节点 ──

@dataclass
class Var:
    """变量引用: $close"""
    name: str

@dataclass
class Num:
    """数值字面量: 20, 0.5"""
    value: float

@dataclass
class Call:
    """函数调用: Mean($close, 20)"""
    fn_name: str
    args: list[ASTNode]

@dataclass
class BinOp:
    """二元运算: a + b, a / b"""
    op: str
    left: ASTNode
    right: ASTNode

@dataclass
class UnaryOp:
    """一元运算: -a"""
    op: str
    operand: ASTNode


ASTNode = Union[Var, Num, Call, BinOp, UnaryOp]


# ── 词法分析 ──

TOKEN_RE = re.compile(r"""
    \s*(?:
        ([+\-*/^()])           |   # 运算符/括号
        (\$[a-zA-Z_]\w*)       |   # 变量 $close
        (\d+\.?\d*)            |   # 数字
        ([A-Za-z_]\w*)         |   # 函数名
        (,)                         # 逗号
    )
""", re.VERBOSE)


def tokenize(expr: str) -> list[tuple[str, str]]:
    """表达式 → token 流。"""
    tokens: list[tuple[str, str]] = []
    for m in TOKEN_RE.finditer(expr):
        op, var, num, name, comma = m.groups()
        if op:   tokens.append(("OP", op))
        elif var: tokens.append(("VAR", var[1:]))  # strip $
        elif num: tokens.append(("NUM", num))
        elif name: tokens.append(("NAME", name))
        elif comma: tokens.append(("COMMA", ","))
    return tokens


# ── 递归下降解析器 ──

class Parser:
    """表达式 → AST。"""

    def __init__(self, tokens: list[tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> tuple[str, str] | None:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type: str | None = None, expected_val: str | None = None):
        tok = self.peek()
        if tok is None:
            raise SyntaxError(f"Unexpected end, expected {expected_type}")
        t, v = tok
        if expected_type and t != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {t}:{v}")
        if expected_val and v != expected_val:
            raise SyntaxError(f"Expected '{expected_val}', got '{v}'")
        self.pos += 1
        return tok

    def parse(self) -> ASTNode:
        return self._expr()

    def _expr(self) -> ASTNode:
        """expr = term (('+'|'-') term)*"""
        left = self._term()
        while (tok := self.peek()) and tok[0] == "OP" and tok[1] in ("+", "-"):
            op = tok[1]
            self.pos += 1
            right = self._term()
            left = BinOp(op=op, left=left, right=right)
        return left

    def _term(self) -> ASTNode:
        """term = factor (('*'|'/') factor)*"""
        left = self._factor()
        while (tok := self.peek()) and tok[0] == "OP" and tok[1] in ("*", "/"):
            op = tok[1]
            self.pos += 1
            right = self._factor()
            left = BinOp(op=op, left=left, right=right)
        return left

    def _factor(self) -> ASTNode:
        """factor = primary ('^' primary)? | '-' factor"""
        tok = self.peek()
        if tok and tok[0] == "OP" and tok[1] == "-":
            self.pos += 1
            return UnaryOp(op="-", operand=self._factor())
        left = self._primary()
        if (tok := self.peek()) and tok[0] == "OP" and tok[1] == "^":
            self.pos += 1
            right = self._factor()  # right-assoc
            return BinOp(op="^", left=left, right=right)
        return left

    def _primary(self) -> ASTNode:
        """primary = NUM | VAR | NAME '(' args ')' | '(' expr ')'"""
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end of expression")

        t, v = tok
        if t == "NUM":
            self.pos += 1
            return Num(value=float(v))
        if t == "VAR":
            self.pos += 1
            return Var(name=v)
        if t == "NAME":
            # Function call
            fn_name = v
            self.pos += 1
            self.consume("OP", "(")
            args = self._args()
            self.consume("OP", ")")
            return Call(fn_name=fn_name, args=args)
        if t == "OP" and v == "(":
            self.pos += 1
            node = self._expr()
            self.consume("OP", ")")
            return node

        raise SyntaxError(f"Unexpected token: {t}:{v}")

    def _args(self) -> list[ASTNode]:
        """args = expr (',' expr)* | ε"""
        args: list[ASTNode] = []
        tok = self.peek()
        if tok and (tok[0] != "OP" or tok[1] != ")"):
            args.append(self._expr())
            while (tok := self.peek()) and tok[0] == "COMMA":
                self.pos += 1
                args.append(self._expr())
        return args


def parse(expr: str) -> ASTNode:
    """解析表达式字符串为 AST。"""
    tokens = tokenize(expr)
    return Parser(tokens).parse()


# ── 求值器 ──

class Evaluator:
    """在 DataFrame 上计算 AST。

    data 可以是:
      - 截面 DataFrame (多股票, 单日): 直接算
      - 时序 DataFrame (单股票): group-by ts_code, 排序后算
    """

    def __init__(self, df: pl.DataFrame):
        self.df = df

    def eval(self, node: ASTNode):
        """求值 AST，返回 Polars Series。"""
        if isinstance(node, Num):
            return node.value  # scalar, will be broadcast later
        if isinstance(node, Var):
            return self.df.get_column(node.name)
        if isinstance(node, BinOp):
            return self._binary(node)
        if isinstance(node, UnaryOp):
            return self._unary(node)
        if isinstance(node, Call):
            return self._call(node)
        raise TypeError(f"Unknown AST node: {type(node)}")

    def _binary(self, node: BinOp):
        left = self.eval(node.left)
        right = self.eval(node.right)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            return left / right
        if node.op == "^":
            return left ** right
        raise ValueError(f"Unknown op: {node.op}")

    def _unary(self, node: UnaryOp):
        operand = self.eval(node.operand)
        if node.op == "-":
            return -operand
        raise ValueError(f"Unknown unary op: {node.op}")

    def _call(self, node: Call):
        fn_name = node.fn_name
        if fn_name not in OPERATOR_MAP:
            raise ValueError(f"Unknown function: {fn_name}")

        fn, is_cs = OPERATOR_MAP[fn_name]
        args = [self.eval(a) for a in node.args]

        if is_cs:
            # 截面算子需要 DataFrame
            return fn(self.df, *args)
        return fn(*args)


# ── 顶层 API ──

def compute_expression(expr: str, df: pl.DataFrame) -> pl.Series:
    """单表达式求值。

    Args:
        expr: 因子表达式, e.g. "Mean($close, 20) / $close - 1"
        df: Polars DataFrame, 需包含表达式引用的列

    Returns:
        Polars Series of factor values.
    """
    ast = parse(expr)
    result = Evaluator(df).eval(ast)
    if not isinstance(result, pl.Series):
        result = pl.Series("factor", [result] * len(df))
    return result.rename(expr[:60])  # truncate long names

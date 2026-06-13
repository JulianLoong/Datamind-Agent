from __future__ import annotations

import ast
import operator
import random
from typing import Any, Callable

from rpl.tools.base import BaseTool, ToolResult
from rpl.tools.builtin.common import ErrorProneMixin

_BINARY_OPS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_numeric(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_numeric(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        left = _eval_numeric(node.left)
        right = _eval_numeric(node.right)
        return _BINARY_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_numeric(node.operand))
    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


class MathCalcTool(ErrorProneMixin, BaseTool):
    def __init__(
        self,
        *,
        error_rate: float = 0.0,
        error_types: list[str] | None = None,
        rng: random.Random | None = None,
    ) -> None:
        ErrorProneMixin.__init__(self, error_rate=error_rate, error_types=error_types, rng=rng)

    @property
    def name(self) -> str:
        return "math_calc"

    @property
    def description(self) -> str:
        return "Evaluate a safe arithmetic expression."

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
            "additionalProperties": False,
        }

    def execute(self, **params: Any) -> ToolResult:
        if injected := self.maybe_injected_error():
            return injected
        expression = params["expression"]
        try:
            tree = ast.parse(expression, mode="eval")
            return ToolResult.ok(_eval_numeric(tree))
        except ZeroDivisionError as exc:
            return ToolResult.fail("division_by_zero", str(exc))
        except Exception as exc:
            return ToolResult.fail("invalid_expression", f"{type(exc).__name__}: {exc}")

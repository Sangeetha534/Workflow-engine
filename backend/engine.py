import ast
import operator

# Allowed operators
OPERATORS = {
    ast.And: operator.and_,
    ast.Or: operator.or_,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Not: operator.not_,
}

def evaluate_condition(condition: str, data: dict) -> bool:
    """
    Safely evaluate a condition string like `amount > 100 and country == 'US'`.
    `data` is the context dictionary containing variables.
    """
    if condition.strip() == "DEFAULT":
        return True
    
    try:
        # Parse expression into AST
        tree = ast.parse(condition, mode='eval')
        return _eval_node(tree.body, data)
    except Exception as e:
        print(f"Error evaluating condition: {condition} - {e}")
        return False

def _eval_node(node, data):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Name):
        if node.id in data:
            return data[node.id]
        if node.id == "True": return True
        if node.id == "False": return False
        if node.id == "None": return None
        raise ValueError(f"Variable '{node.id}' not found in data")
    elif isinstance(node, ast.Compare):
        left = _eval_node(node.left, data)
        # Handle multiple comparators (e.g., 0 < x < 10)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, data)
            op_func = OPERATORS.get(type(op))
            if not op_func:
                raise TypeError(f"Unsupported operator: {type(op)}")
            if not op_func(left, right):
                return False
            left = right
        return True
    elif isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(_eval_node(value, data) for value in node.values)
        elif isinstance(node.op, ast.Or):
            return any(_eval_node(value, data) for value in node.values)
    elif isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return not _eval_node(node.operand, data)
    
    raise TypeError(f"Unsupported syntax: {type(node)}")

if __name__ == "__main__":
    context = {"amount": 150, "country": "US"}
    print(evaluate_condition("amount > 100 and country == 'US'", context)) # True
    print(evaluate_condition("amount < 100", context)) # False
    print(evaluate_condition("DEFAULT", context)) # True

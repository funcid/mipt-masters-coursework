import re
from typing import Optional


class Calculator:
    def __init__(self):
        self.current_expression: Optional[str] = None
        self.result: Optional[float] = None
    
    def add(self, a: float, b: float) -> float:
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Деление на ноль невозможно")
        return a / b
    
    def set_expression(self, expression: str) -> None:
        self.current_expression = expression.strip()
        self.result = None
    
    def get_expression(self) -> Optional[str]:
        return self.current_expression
    
    def _tokenize(self, expression: str) -> list:
        pattern = r'\d+\.?\d*|[+\-*/()]|[a-zA-Z_]\w*'
        return re.findall(pattern, expression)
    
    def _is_number(self, token: str) -> bool:
        try:
            float(token)
            return True
        except ValueError:
            return False
    
    def _precedence(self, op: str) -> int:
        if op in ('+', '-'):
            return 1
        elif op in ('*', '/'):
            return 2
        return 0
    
    def _apply_operator(self, a: float, b: float, op: str) -> float:
        operations = {
            '+': self.add,
            '-': self.subtract,
            '*': self.multiply,
            '/': self.divide
        }
        if op not in operations:
            raise ValueError(f"Неизвестный оператор: {op}")
        return operations[op](a, b)
    
    def _evaluate_tokens(self, tokens: list) -> float:
        values = []
        operators = []
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if self._is_number(token):
                values.append(float(token))
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    self._process_operator(values, operators)
                operators.pop()
            elif token in ('+', '-', '*', '/'):
                if token == '-' and (i == 0 or tokens[i-1] == '('):
                    values.append(0.0)
                
                while (operators and 
                       operators[-1] != '(' and 
                       self._precedence(operators[-1]) >= self._precedence(token)):
                    self._process_operator(values, operators)
                operators.append(token)
            
            i += 1
        
        while operators:
            self._process_operator(values, operators)
        
        if len(values) != 1:
            raise ValueError("Неверное выражение")
        
        return values[0]
    
    def _process_operator(self, values: list, operators: list) -> None:
        if len(values) < 2:
            raise ValueError("Недостаточно операндов")
        
        op = operators.pop()
        b = values.pop()
        a = values.pop()
        values.append(self._apply_operator(a, b, op))
    
    def evaluate_expression(self, expression: Optional[str] = None) -> float:
        if expression is None:
            expression = self.current_expression
        
        if expression is None:
            raise ValueError("Выражение не установлено")
        
        expression = expression.replace(' ', '')
        tokens = self._tokenize(expression)
        
        if not tokens:
            raise ValueError("Пустое выражение")
        
        result = self._evaluate_tokens(tokens)
        
        self.result = result
        if self.current_expression is None:
            self.current_expression = expression
        
        return result
    
    def execute(self) -> float:
        if self.current_expression is None:
            raise ValueError("Выражение не установлено")
        return self.evaluate_expression(self.current_expression)


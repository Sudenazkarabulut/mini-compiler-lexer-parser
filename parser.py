class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.symbol_table = {} 
        self.errors = []
        self.ast = []

    def get_current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def match(self, expected_type):
        token = self.get_current_token()
        if token and token['type'] == expected_type:
            self.pos += 1
            return token
        else:
            actual = token['type'] if token else "END"
            line = token['line'] if token else "unknown"
            self.errors.append(f"Syntax Error: Expected {expected_type}, found {actual} at line {line}")
            return None

    def parse(self):
        while self.pos < len(self.tokens):
            token = self.get_current_token()
            if not token: break

            stmt = None
            if token['type'] == 'KEYWORD':
                if token['value'] in ['int', 'float']: stmt = self.parse_declaration()
                elif token['value'] == 'print': stmt = self.parse_print()
                elif token['value'] == 'if': stmt = self.parse_if()
                elif token['value'] == 'while': stmt = self.parse_while()
                else: self.pos += 1
            elif token['type'] == 'ID': 
                stmt = self.parse_assignment()
            elif token['type'] == 'DELIMITER' and token['value'] == ';':
                self.pos += 1 # to ignore extra semicolons
            else:
                self.errors.append(f"Syntax Error: Unexpected token '{token['value']}' at line {token['line']}")
                self.pos += 1 

            if stmt: self.ast.append(stmt) # add each statement to the ast tree
    
    def parse_if(self):
        self.match('KEYWORD') 
        self.match('DELIMITER') 
        cond = self.parse_comparison() 
        self.match('DELIMITER') 
        self.match('DELIMITER') 
        body = self.parse_block()      
        self.match('DELIMITER') 
        
        else_body = []
        # Check for ELSE
        token = self.get_current_token()
        if token and token['value'] == 'else':
            self.match('KEYWORD')   # else
            self.match('DELIMITER') # {
            else_body = self.parse_block()
            self.match('DELIMITER') # }
        return ['IF', cond, body, else_body]

    def parse_while(self):
        self.match('KEYWORD')  
        self.match('DELIMITER') 
        cond = self.parse_comparison() 
        self.match('DELIMITER') 
        self.match('DELIMITER') 
        body = self.parse_block()
        self.match('DELIMITER') 
        return ['WHILE', cond, body]

    def parse_print(self):
        self.match('KEYWORD')  
        self.match('DELIMITER') 
        
        token = self.get_current_token()
        if token and token['type'] == 'STRING':
            val = self.match('STRING')['value']
            node = ['PRINT', val]
        else:
            val = self.parse_arithmatic()
            node = ['PRINT', val]
            
        self.match('DELIMITER') 
        self.match('DELIMITER') 
        return node

    # Helper function to parse multiple lines inside { }
    def parse_block(self):
        block_ast = []
        while self.get_current_token() and self.get_current_token()['value'] != '}':
            token = self.get_current_token()
            if not token: break
            
            stmt = None
            if token['type'] == 'ID': 
                stmt = self.parse_assignment()
            elif token['type'] == 'KEYWORD':
                if token['value'] == 'print': stmt = self.parse_print()
                elif token['value'] == 'if': stmt = self.parse_if()
                elif token['value'] == 'while': stmt = self.parse_while()
                else: self.pos += 1
            else:
                self.pos += 1
            if stmt: block_ast.append(stmt)
        return block_ast

    def parse_declaration(self):
        type_token = self.match('KEYWORD') # int
        id_token = self.match('ID')       # x
        
        if id_token:
            variable = id_token['value']
            #  for duplicate declarations check
            if variable in self.symbol_table:
                self.errors.append(f"Semantic Error: Variable '{variable}' already declared at line {id_token['line']}.")
            else:
                address = f"0x{1000 + len(self.symbol_table) * 4}"
                self.symbol_table[variable] = {
                    'type': type_token['value'], 
                    'line': id_token['line'],
                    'address': address
                    }
        
        self.match('DELIMITER')
        return ['DECL', type_token['value'], id_token['value'] if id_token else None]

    def parse_assignment(self):
        id_token = self.match('ID')
        var_name = id_token['value'] if id_token else None
        
        if id_token and var_name not in self.symbol_table:
            self.errors.append(f"Semantic Error: Variable '{var_name}' used before declaration at line {id_token['line']}.")
        
        self.match('OPERATOR') 
        value_node = self.parse_arithmatic() 
        
        # check Type Mismatch (full expression tree)
        if id_token and var_name in self.symbol_table:
            var_type = self.symbol_table[var_name]['type']
            expr_type = self.infer_expression_type(value_node)
            if expr_type == 'string' and var_type in ('int', 'float'):
                self.errors.append(f"Semantic Error: Type Mismatch. Cannot assign String to {var_type} '{var_name}' at line {id_token['line']}.")
            elif var_type == 'int' and expr_type == 'float':
                self.errors.append(f"Semantic Error: Cannot assign float expression to int variable '{var_name}' at line {id_token['line']}.")

        self.match('DELIMITER')
        return ['ASSIGN', var_name, value_node]

    def infer_expression_type(self, node):
        """Return the resulting type of an expression AST node."""
        if node is None:
            return None
        if isinstance(node, str):
            if node.startswith('"'):
                return 'string'
            if self._is_float_literal(node):
                return 'float'
            if node.isdigit() or (node.startswith('-') and node[1:].isdigit()):
                return 'int'
            if node in self.symbol_table:
                return self.symbol_table[node]['type']
            return None
        if isinstance(node, list) and node and node[0] == 'BINOP':
            _, left, op, right = node
            if op in ('+', '-', '*', '/'):
                left_t = self.infer_expression_type(left)
                right_t = self.infer_expression_type(right)
                return self.arithmetic_result_type(left_t, right_t)
        return None

    def _is_float_literal(self, value):
        if '.' not in value:
            return False
        parts = value.split('.', 1)
        return len(parts) == 2 and parts[0].lstrip('-').isdigit() and parts[1].isdigit()

    def arithmetic_result_type(self, left_t, right_t):
        if left_t is None or right_t is None:
            return None
        if left_t == 'string' or right_t == 'string':
            return None
        if left_t == 'float' or right_t == 'float':
            return 'float'
        if left_t == 'int' and right_t == 'int':
            return 'int'
        return None

 # --- MATH LOGIC ---
    def parse_arithmatic(self):
        left = self.parse_term()
        while self.get_current_token() and self.get_current_token()['value'] in ['+', '-']:
            op = self.match('OPERATOR')['value']
            right = self.parse_term()
            left = ['BINOP', left, op, right]
        return left
    
    def parse_comparison(self):
        left = self.parse_arithmatic() 
        comparisons = ['==', '!=', '<', '>', '<=', '>=', '&&', '||']
        while self.get_current_token() and self.get_current_token()['value'] in comparisons:
            op = self.match('OPERATOR')['value']
            right = self.parse_arithmatic()
            left = ['BINOP', left, op, right]
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.get_current_token() and self.get_current_token()['value'] in ['*', '/']:
            op = self.match('OPERATOR')['value']
            right = self.parse_factor()
            left = ['BINOP', left, op, right]
        return left

    def parse_factor(self):
        token = self.get_current_token()
        if not token: return None

        if token['type'] in ['INT_LIT', 'FLOAT_LIT']:
            return self.match(token['type'])['value']
        elif token and token['type'] == 'ID':
            if token['value'] not in self.symbol_table:
                self.errors.append(f"Semantic Error: {token['value']} undefined")
            return self.match('ID')['value']
        elif token['type'] == 'STRING':
            return self.match('STRING')['value']
        elif token['value'] == '(':
            self.match('DELIMITER')
            node = self.parse_arithmatic()
            self.match('DELIMITER')
            return node
        elif token['type'] == 'STRING':
            return self.match('STRING')['value']
        return None
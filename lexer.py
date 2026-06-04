import re

# These are the "rules" for our language tokens
TOKEN_TYPES = [
    ('COMMENT',    r'//.*'),  
    ('KEYWORD',    r'\b(int|float|if|else|while|print)\b'),
    ('ID',         r'[a-zA-Z_][a-zA-Z0-9_]*'),  # Variable names
    ('FLOAT_LIT',  r'\d+\.\d+'),                # Numbers like 3.14
    ('INT_LIT',    r'\d+'),                     # Numbers like 10
    ('OPERATOR',   r'==|!=|<=|>=|&&|\|\||[+\-*/=<>]'),  # Math and Logic
    ('DELIMITER',  r'[;(){}]'),                 # Punctuation
    ('STRING',     r'"[^"]*"'),                 # Text in quotes
    ('SKIP',       r'[ \t]+'),                  # Spaces and tabs
    ('NEWLINE',    r'\n'),                      # Line breaks
    ('MISMATCH',   r'.'),                       # Anything else (Errors)
]

def tokenize(code):
    tokens = []
    errors = []
    line_num = 1
    
    # combining all rules into one big search pattern
    master_regex = '|'.join('(?P<%s>%s)' % pair for pair in TOKEN_TYPES)
    
    for mo in re.finditer(master_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'SKIP' or kind == 'COMMENT':
            continue
        elif kind == 'NEWLINE':
            line_num += 1
        elif kind == 'MISMATCH':
            errors.append(f"Lexical Error: Illegal character '{value}' at line {line_num}")
        else:
            tokens.append({'line': line_num, 'type': kind, 'value': value})
    
    return tokens, errors

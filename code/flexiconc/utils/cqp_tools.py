import re

# --------------- Tokenizer and Parser ---------------

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        if s[i].isspace(): i += 1
        elif s[i] == '@':
            yield Token('AT'); i += 1
        elif s[i] == ':':
            yield Token('COLON'); i += 1
        elif s[i] == '[': yield Token('LBRACK'); i += 1
        elif s[i] == ']': yield Token('RBRACK'); i += 1
        elif s[i] == '(': yield Token('LPAREN'); i += 1
        elif s[i] == ')': yield Token('RPAREN'); i += 1
        elif s[i] == '=':
            if i > 0 and s[i-1] == '!': i += 1; continue
            yield Token('EQUAL'); i += 1
        elif s[i] == '!' and i+1 < n and s[i+1] == '=':
            yield Token('NEQ'); i += 2
        elif s[i] == '!': yield Token('NOT'); i += 1
        elif s[i] == '&': yield Token('AND'); i += 1
        elif s[i] == '|': yield Token('OR'); i += 1
        elif s[i] == '%':
            i += 1
            flags = ''
            while i < n and s[i].isalpha():
                flags += s[i]; i += 1
            if not flags: raise Exception("Expected flags after '%'")
            yield Token('FLAGS', flags)
        elif s[i] in '?+*':
            yield Token('QUANT', s[i]); i += 1
        elif s[i] == '{':
            i += 1; start = i
            while i < n and s[i] != '}': i += 1
            if i == n: raise Exception("Unclosed quantifier")
            yield Token('QUANT', '{' + s[start:i] + '}'); i += 1
        elif s[i] == '"' or s[i] == "'":
            quote = s[i]; i += 1
            chars = []
            while i < n:
                if s[i] == '\\':
                    i += 1
                    if i == n: raise Exception("Unclosed escape")
                    chars.append(s[i])
                    i += 1
                elif s[i] == quote:
                    if i + 1 < n and s[i+1] == quote:
                        chars.append(quote)
                        i += 2
                    else:
                        break
                else:
                    chars.append(s[i])
                    i += 1
            if i == n: raise Exception("Unclosed string")
            yield Token('STRING', ''.join(chars))
            i += 1
        elif s[i].isalpha():
            start = i
            while i < n and (s[i].isalnum() or s[i] == '_'): i += 1
            yield Token('IDENT', s[start:i])
        else: raise Exception(f"Unexpected character: {s[i]}")
    yield Token('EOF')

class Parser:
    def __init__(self, tokens, default_attr="word"):
        self.tokens = list(tokens)
        self.pos = 0
        self.default_attr = default_attr
    @property
    def tok(self):
        return self.tokens[self.pos]
    def eat(self, type_):
        if self.tok.type == type_:
            self.pos += 1
        else:
            raise Exception(f"Expected {type_}, got {self.tok.type}")
    def lookahead(self, offset=1):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return Token('EOF')
    def parse_query(self):
        res = []
        while self.is_token_start():
            pattern, quant = self.parse_labeled_token()
            res.append({'pattern': pattern, 'quant': quant})
        if self.tok.type != 'EOF': raise Exception("Trailing garbage")
        return res
    def is_token_start(self):
        return (
            self.tok.type in {'LBRACK', 'STRING', 'AT', 'IDENT'}
        )
    def parse_labeled_token(self):
        label = None
        is_target = False
        if self.tok.type == 'AT':
            self.eat('AT')
            is_target = True
        # label:token
        if self.tok.type == 'IDENT' and self.lookahead().type == 'COLON':
            label = self.tok.value
            self.eat('IDENT')
            self.eat('COLON')
        token = self.parse_token()
        quant = self.parse_quant()
        return (
            {'label': label, 'is_target': is_target, 'token': token},
            quant
        )
    def parse_token(self):
        if self.tok.type == 'LBRACK':
            self.eat('LBRACK')
            if self.tok.type == 'RBRACK':
                self.eat('RBRACK')
                return {'type': 'any'}
            node = self.parse_constraint_expr()
            self.eat('RBRACK')
            return node
        elif self.tok.type == 'STRING':
            value = self.tok.value
            self.eat('STRING')
            flags = None
            if self.tok.type == 'FLAGS':
                flags = self.tok.value
                self.eat('FLAGS')
            return {'type': 'eq', 'attr': self.default_attr, 'value': value, 'flags': flags}
        else:
            raise Exception("Expected '[' or string")
    def parse_quant(self):
        if self.tok.type == 'QUANT':
            val = self.tok.value
            self.eat('QUANT')
            return val
        return None
    def parse_constraint_expr(self):
        node = self.parse_constraint_and()
        while self.tok.type == 'OR':
            self.eat('OR')
            right = self.parse_constraint_and()
            node = {'type': 'or', 'left': node, 'right': right}
        return node
    def parse_constraint_and(self):
        node = self.parse_constraint_not()
        while self.tok.type == 'AND':
            self.eat('AND')
            right = self.parse_constraint_not()
            node = {'type': 'and', 'left': node, 'right': right}
        return node
    def parse_constraint_not(self):
        if self.tok.type == 'NOT':
            self.eat('NOT')
            node = self.parse_constraint_not()
            return {'type': 'not', 'expr': node}
        else:
            return self.parse_constraint_atom()
    def parse_constraint_atom(self):
        if self.tok.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.parse_constraint_expr()
            self.eat('RPAREN')
            return node
        elif self.tok.type == 'STRING':
            value = self.tok.value
            self.eat('STRING')
            flags = None
            if self.tok.type == 'FLAGS':
                flags = self.tok.value
                self.eat('FLAGS')
            return {'type': 'eq', 'attr': self.default_attr, 'value': value, 'flags': flags}
        elif self.tok.type == 'IDENT':
            attr = self.tok.value
            self.eat('IDENT')
            if self.tok.type == 'EQUAL':
                self.eat('EQUAL')
                val = self.tok.value
                self.eat('STRING')
                flags = None
                if self.tok.type == 'FLAGS':
                    flags = self.tok.value
                    self.eat('FLAGS')
                return {'type': 'eq', 'attr': attr, 'value': val, 'flags': flags}
            elif self.tok.type == 'NEQ':
                self.eat('NEQ')
                val = self.tok.value
                self.eat('STRING')
                flags = None
                if self.tok.type == 'FLAGS':
                    flags = self.tok.value
                    self.eat('FLAGS')
                return {'type': 'neq', 'attr': attr, 'value': val, 'flags': flags}
            else:
                # structural attribute/region test
                return {'type': 'region', 'name': attr}
        else:
            raise Exception("Expected atomic constraint")
def parse_cqp(query, default_attr="word"):
    tokens = tokenize(query)
    parser = Parser(tokens, default_attr=default_attr)
    return parser.parse_query()

# --------------- Pandas Matching Function ---------------

def match_token_df(df, token, as_mask=False):
    import re

    node_type = token['type']
    if node_type == 'any':
        mask = pd.Series([True] * len(df), index=df.index)
    elif node_type == 'region':
        mask = df[token['name']].astype(bool)
    elif node_type == 'not':
        mask = ~match_token_df(df, token['expr'], as_mask=True)
    elif node_type == 'and':
        left = match_token_df(df, token['left'], as_mask=True)
        right = match_token_df(df, token['right'], as_mask=True)
        mask = left & right
    elif node_type == 'or':
        left = match_token_df(df, token['left'], as_mask=True)
        right = match_token_df(df, token['right'], as_mask=True)
        mask = left | right
    elif node_type in ('eq', 'neq'):
        attr, val, flags = token['attr'], token['value'], token['flags'] or ""
        col = df[attr].astype(str)
        re_flags = 0
        if 'c' in flags:
            re_flags |= re.IGNORECASE
        match = col.str.fullmatch(val, flags=re_flags)
        mask = match if node_type == 'eq' else ~match
    else:
        raise Exception(f"Unknown node type: {node_type}")

    if as_mask:
        return mask
    else:
        return mask[mask].index.tolist()

# --------------- SQLite Matching Function ---------------

def match_token_sqlite(con, table, token):
    import re
    def regexp(pattern, string):
        if string is None:
            return False
        return re.fullmatch(pattern, string) is not None

    con.create_function("REGEXP", 2, regexp)

    if token['type'] == 'any':
        q = f"SELECT rowid FROM {table}"
        return [row[0] for row in con.execute(q)]
    if token['type'] == 'region':
        sql = f"SELECT rowid FROM {table} WHERE {token['name']}"
        return [row[0] for row in con.execute(sql)]
    if token['type'] == 'not':
        all_rows = set(match_token_sqlite(con, table, {'type': 'any'}))
        x = set(match_token_sqlite(con, table, token['expr']))
        return list(all_rows - x)
    if token['type'] == 'and':
        l = set(match_token_sqlite(con, table, token['left']))
        r = set(match_token_sqlite(con, table, token['right']))
        return list(l & r)
    if token['type'] == 'or':
        l = set(match_token_sqlite(con, table, token['left']))
        r = set(match_token_sqlite(con, table, token['right']))
        return list(l | r)
    if token['type'] in ('eq', 'neq'):
        attr, val, flags = token['attr'], token['value'], token['flags'] or ""
        params = [val]
        if token['type'] == 'eq':
            clause = f"{attr} REGEXP ?" if 'c' not in flags else f"LOWER({attr}) REGEXP LOWER(?)"
        else:
            clause = f"NOT {attr} REGEXP ?" if 'c' not in flags else f"NOT LOWER({attr}) REGEXP LOWER(?)"
        sql = f"SELECT rowid FROM {table} WHERE {clause}"
        return [row[0] for row in con.execute(sql, params)]
    raise Exception(f"Unknown node type: {token['type']}")

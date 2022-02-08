TT_INT = 'INT'  # int
TT_FLOAT = 'FLOAT'  # float
TT_STRING = 'STRING'  # string
TT_IDENTIFIER = 'IDENTIFIER'  # 变量
TT_KEYWORD = 'KEYWORD'  # 关键字
TT_PLUS = 'PLUS'  # +
TT_MINUS = 'MINUS'  # -
TT_MUL = 'MUL'  # *
TT_DIV = 'DIV'  # /
TT_POW = 'POW'  # ^
TT_EQ = 'EQ'  # =
TT_LPAREN = 'LPAREN'  # (
TT_RPAREN = 'RPAREN'  # )
TT_LSQUARE = 'LSQUARE'
TT_RSQUARE = 'RSQUARE'
TT_EE = 'EE'  # ==
TT_NE = 'NE'  # !=
TT_LT = 'LT'  # >
TT_GT = 'GT'  # <
TT_LTE = 'LTE'  # >=
TT_GTE = 'GTE'  # <=
TT_COMMA = 'COMMA'
TT_ARROW = 'ARROW'
TT_NEWLINE = 'NEWLINE'
TT_EOF = 'EOF'

KEYWORDS = [
    'VAR',
    'AND',
    'OR',
    'NOT',
    'IF',
    'ELIF',
    'ELSE',
    'FOR',
    'TO',
    'STEP',
    'WHILE',
    'FUN',
    'THEN',
    'END',
    'RETURN',  # 拥有净身出户的权力
    'CONTINUE',
    'BREAK',
]


class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        # 可选参数 value, pos_start, pos_end
        self.type = type_
        self.value = value

        # 若没有传入 pos_end，比如 1，此时 pos_start == 1 且 pos_end == 1
        if pos_start:
            self.pos_start = pos_start.copy()  # 调用 copy 方法
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end.copy()

    # 判断 type-value 是否一致
    def matches(self, type_, value):
        return self.type == type_ and self.value == value

    def __repr__(self):
        if self.value:
            return f'{self.type}:{self.value}'
        return f'{self.type}'

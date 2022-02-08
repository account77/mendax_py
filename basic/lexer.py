#######################################
# LEXER
# 词法分析，解析生成 token
#######################################


class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)  # Position 类实例化 -> pos 对象
        self.current_char = None
        self.advance()  # 调用该对象的 advance 方法，往前读取

    def advance(self):
        self.pos.advance(self.current_char)
        # 若 text 未被读完，则将 current_char 定位到当前索引
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(
            self.text) else None

    # 解析 token
    def make_tokens(self):
        tokens = []  # 把 token 对象（们）加入列表

        while self.current_char != None:
            # 忽略空格和制表符
            if self.current_char in ' \t':
                self.advance()
            # 处理注释相关逻辑
            elif self.current_char == '#':
                self.skip_comment()
            elif self.current_char in ';\n':
                # 向列表 tokens 追加一个 TT_NEWLINE 对象
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()  # 此时，不要忘记应当继续往前读取
            elif self.current_char in DIGITS:  # 数字
                tokens.append(self.make_number())
            elif self.current_char in LETTERS:  # 字母
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':  # ->
                tokens.append(self.make_minus_or_arrow())
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '[':
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == '!':
                token, error = self.make_not_equals()
                if error:
                    return [], error
                tokens.append(token)
            elif self.current_char == '=':  # 为变量赋值
                tokens.append(self.make_equals())
            elif self.current_char == '<':
                tokens.append(self.make_less_than())
            elif self.current_char == '>':
                tokens.append(self.make_greater_than())
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()
            else:
                # 若匹配失败，则报告非法字符错误
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

        # 表示匹配结束
        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    # 解析数字
    def make_number(self):
        num_str = ''  # 跟踪数字
        dot_count = 0  # 跟踪小数点
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + '.':
            # 域：自然数 + 小数点
            if self.current_char == '.':
                # 不能有两个小数点
                if dot_count == 1:
                    break
                dot_count += 1
            num_str += self.current_char
            self.advance()

        # 整数类型 ｜ 浮点数类型
        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

    # 解析字符串
    def make_string(self):
        string = ''
        pos_start = self.pos.copy()
        escape_character = False  # 判断是否为转义字符
        self.advance()

        escape_characters = {  # 字典，用以表示其映射关系
            'n': '\n',  # 换行
            't': '\t'   # 缩进
        }

        # " abc \"d\" \n \t "
        # 或者不是转义字符
        while self.current_char != None and (self.current_char != '"' or escape_character):
            # 比如 \n，当读取到 / 时，escape_character 会被置为 true
            if escape_character:
                # 依据字典来获取当前的字符串，若获取失败，则把自身返回。例如，获取失败的话，就是这种情况 \\
                string += escape_characters.get(self.current_char,
                                                self.current_char)
            else:
                if self.current_char == '\\':  # python 语法需要对 / 做转义处理，// --> /
                    escape_character = True
                # 啥也不是，普普通通
                else:
                    string += self.current_char
            self.advance()
            escape_character = False  # 不要忘记把它返回为 False

        self.advance()
        return Token(TT_STRING, string, pos_start, self.pos)  # string 就是我们取得的值

    # 解析变量
    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        # VAR varible = 1024;id_str = 'varible' （变量就是一坨字符）
        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()

        # 不是关键字就是变量
        # if id_str in KEYWORDS: { tok_type = TT_KEYWORD } else: { tok_type = TT_IDENTIFIER }
        tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)

    # 解析 ->
    def make_minus_or_arrow(self):
        tok_type = TT_MINUS
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '>':
            self.advance()
            tok_type = TT_ARROW

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    # 解析 !=
    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None

        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")

    # 解析 = 和 ==
    def make_equals(self):
        tok_type = TT_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_EE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    # 解析 < 和 <=
    def make_less_than(self):
        tok_type = TT_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_LTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    # 解析 > 和 >=
    def make_greater_than(self):
        tok_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_GTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    # 跳过注释部分
    def skip_comment(self):
        self.advance()

        while self.current_char != '\n':
            self.advance()

        self.advance()


#######################################
# IMPORTS
#######################################

from data.contants import *
from util.position import Position
from util.error import IllegalCharError, ExpectedCharError
from data.tokens import *
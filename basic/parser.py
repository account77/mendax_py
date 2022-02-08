#######################################
# PARSER
# 语法分析，构建抽象语法树
#######################################


class Parser:
    # 初始化新创建对象的状态，在对象被创建以后便立即调用
    def __init__(self, tokens):
        self.tokens = tokens
        # 设计用因：使得每次初始化时自动往前读取 token 列表
        self.tok_idx = -1  # 索引从 -1 开始
        self.advance()  # 随后立即调用 advance 函数

    def advance(self):
        self.tok_idx += 1
        self.update_current_tok()
        return self.current_tok

    def reverse(self, amount=1):
        self.tok_idx -= amount
        self.update_current_tok()
        return self.current_tok

    # 更新当前索引值
    def update_current_tok(self):
        if self.tok_idx >= 0 and self.tok_idx < len(self.tokens):  # tokens 列表
            self.current_tok = self.tokens[self.tok_idx]

    def parse(self):
        res = self.statements()  # 根据已经写好的 BNF 文法可知，statements 函数位于起始处；自此便开始了递归向下的处理
        # 如果存在 error 并且没有读到 EOF，则报告错误
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Token cannot appear after previous tokens"
            ))
        return res

    ###################################

    # statements  ->  NEWLINE* statement (NEWLINE+ statement)* NEWLINE*
    def statements(self):
        res = ParseResult()  # 实例化 ParseResult 类
        statements = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

        statement = res.register(self.statement())
        if res.error:
            return res
        statements.append(statement)

        more_statements = True

        while True:
            newline_count = 0
            while self.current_tok.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()
                newline_count += 1
            if newline_count == 0:
                more_statements = False

            if not more_statements:
                break
            statement = res.try_register(self.statement())
            if not statement:
                self.reverse(res.to_reverse_count)
                more_statements = False
                continue
            statements.append(statement)

        return res.success(ListNode(
            statements,
            pos_start,
            self.current_tok.pos_end.copy()
        ))

    # statement  ->  KEYWORD:RETURN expr?
    #		     ->  KEYWORD:CONTINUE
    #	         ->  KEYWORD:BREAK
    #		     ->  expr
    def statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        # 匹配 RETURN 关键字
        if self.current_tok.matches(TT_KEYWORD, 'RETURN'):
            res.register_advancement()
            self.advance()

            expr = res.try_register(self.expr())
            if not expr:
                self.reverse(res.to_reverse_count)
            return res.success(ReturnNode(expr, pos_start, self.current_tok.pos_start.copy()))

        # 匹配 RETURN 关键字
        if self.current_tok.matches(TT_KEYWORD, 'CONTINUE'):
            res.register_advancement()
            self.advance()
            return res.success(ContinueNode(pos_start, self.current_tok.pos_start.copy()))

        # 匹配 BREAK 关键字
        if self.current_tok.matches(TT_KEYWORD, 'BREAK'):
            res.register_advancement()
            self.advance()
            return res.success(BreakNode(pos_start, self.current_tok.pos_start.copy()))

        expr = res.register(self.expr())
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'RETURN', 'CONTINUE', 'BREAK', 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
            ))
        return res.success(expr)

    # expr  ->  KEYWORD:VAR IDENTIFIER EQ expr
    #       ->  comp-expr ((KEYWORD:AND|KEYWORD:OR) comp-expr)*
    def expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, 'VAR'):
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier"  # 因为此时按照文法来讲，应为变量名
                ))

            var_name = self.current_tok  # 变量名
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_EQ:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))

            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            # 该句文法结束
            return res.success(VarAssignNode(var_name, expr))

        # 依照文法往下走
        node = res.register(self.bin_op(
            self.comp_expr, ((TT_KEYWORD, 'AND'), (TT_KEYWORD, 'OR'))))

        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
            ))

        return res.success(node)

    # comp-expr  ->  NOT comp-expr
    #            ->  arith-expr ((EE|LT|GT|LTE|GTE) arith-expr)*
    def comp_expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, 'NOT'):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error:
                return res
            return res.success(UnaryOpNode(op_tok, node))

        node = res.register(self.bin_op(
            self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))

        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected int, float, identifier, '+', '-', '(', '[', 'IF', 'FOR', 'WHILE', 'FUN' or 'NOT'"
            ))

        return res.success(node)

    # arith-expr  ->  term ((PLUS|MINUS) term)*
    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    # term  ->  factor ((MUL|DIV) factor)*
    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    # 根据文法（grammar.txt）实现函数之间的递归调用
    # factor ->  (PLUS|MINUS) factor -1 == --1 == ---1
    #	     ->  power
    def factor(self):
        res = ParseResult()  # ParseResult 返回的是对象
        tok = self.current_tok

        # factor -> (PLUS|MINUS) factor -1 == --1 == ---1
        if tok.type in (TT_PLUS, TT_MINUS):
            res.register_advancement()  # 便于进程在出错时的回滚操作
            self.advance()
            factor = res.register(self.factor())  # 调用自身
            # 因为 factor() 为非终止符，所以会继续向前匹配，在这个过程中可能存在 error
            if res.error:
                return res
            # 一元操作
            return res.success(UnaryOpNode(tok, factor))

        # 下一句文法，调用 self.power 函数
        return self.power()

    # power  ->  call (POWf actor)*
    def power(self):
        return self.bin_op(self.call, (TT_POW,), self.factor)

    # call  ->  atom (LPAREN (expr (COMMA expr)*)? RPAREN)?
    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error:
            return res

        if self.current_tok.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            arg_nodes = []

            if self.current_tok.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ')', 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
                    ))

                while self.current_tok.type == TT_COMMA:
                    res.register_advancement()
                    self.advance()

                    arg_nodes.append(res.register(self.expr()))
                    if res.error:
                        return res

                if self.current_tok.type != TT_RPAREN:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        f"Expected ',' or ')'"
                    ))

                res.register_advancement()
                self.advance()
            return res.success(CallNode(atom, arg_nodes))
        return res.success(atom)

    # atom  ->  INT|FLOAT|STRING|IDENTIFIER
    #       ->  LPAREN expr RPAREN
    #       ->  list-expr
    #       ->  if-expr
    #       ->  for-expr
    #       ->  while-expr
    #       ->  func-def
    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(tok))

        elif tok.type == TT_STRING:
            res.register_advancement()
            self.advance()
            return res.success(StringNode(tok))

        elif tok.type == TT_IDENTIFIER:
            res.register_advancement()
            self.advance()
            return res.success(VarAccessNode(tok))

        elif tok.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))

        elif tok.type == TT_LSQUARE:
            list_expr = res.register(self.list_expr())
            if res.error:
                return res
            return res.success(list_expr)

        elif tok.matches(TT_KEYWORD, 'IF'):
            if_expr = res.register(self.if_expr())
            if res.error:
                return res
            return res.success(if_expr)

        elif tok.matches(TT_KEYWORD, 'FOR'):
            for_expr = res.register(self.for_expr())
            if res.error:
                return res
            return res.success(for_expr)

        elif tok.matches(TT_KEYWORD, 'WHILE'):
            while_expr = res.register(self.while_expr())
            if res.error:
                return res
            return res.success(while_expr)

        elif tok.matches(TT_KEYWORD, 'FUN'):
            func_def = res.register(self.func_def())
            if res.error:
                return res
            return res.success(func_def)

        return res.failure(InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected int, float, identifier, '+', '-', '(', '[', IF', 'FOR', 'WHILE', 'FUN'"
        ))

    # list-expr  ->  LSQUARE (expr (COMMA expr)*)? RSQUARE
    def list_expr(self):
        res = ParseResult()
        element_nodes = []  # 存放列表中的元素 [1, 2, 3]
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LSQUARE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '['"
            ))

        res.register_advancement()
        self.advance()

        # 若 self.current_tok.type == TT_RSQUARE 则说明为空列表 []
        if self.current_tok.type == TT_RSQUARE:
            res.register_advancement()
            self.advance()
        else:
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ']', 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
                ))

            while self.current_tok.type == TT_COMMA:
                res.register_advancement()
                self.advance()

                element_nodes.append(res.register(self.expr()))
                if res.error:
                    return res

            if self.current_tok.type != TT_RSQUARE:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected ',' or ']'"
                ))

            res.register_advancement()
            self.advance()

        return res.success(ListNode(
            element_nodes,
            pos_start,
            self.current_tok.pos_end.copy()
        ))

    # if-expr  ->  KEYWORD:IF expr KEYWORD:THEN
    #              (statement if-expr-b|if-expr-c?)
    #          |   (NEWLINE statements KEYWORD:END|if-expr-b|if-expr-c)
    def if_expr(self):
        res = ParseResult()
        all_cases = res.register(self.if_expr_cases('IF'))
        if res.error:
            return res
        cases, else_case = all_cases
        return res.success(IfNode(cases, else_case))

    # if-expr-b  ->  KEYWORD:ELIF expr KEYWORD:THEN
    #                 (statement if-expr-b|if-expr-c?)
    #            |   (NEWLINE statements KEYWORD:END|if-expr-b|if-expr-c)
    def if_expr_b(self):
        return self.if_expr_cases('ELIF')

    # if-expr-c  ->  KEYWORD:ELSE
    #                statement
    #            |   (NEWLINE statements KEYWORD:END)
    def if_expr_c(self):
        res = ParseResult()
        else_case = None

        if self.current_tok.matches(TT_KEYWORD, 'ELSE'):
            res.register_advancement()
            self.advance()

            if self.current_tok.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()

                statements = res.register(self.statements())
                if res.error:
                    return res
                else_case = (statements, True)

                # 若语句至此没有结束
                if self.current_tok.matches(TT_KEYWORD, 'END'):
                    res.register_advancement()
                    self.advance()
                else:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected 'END'"
                    ))
            else:
                expr = res.register(self.statement())
                if res.error:
                    return res
                else_case = (expr, False)

        return res.success(else_case)

    def if_expr_b_or_c(self):
        res = ParseResult()
        cases, else_case = [], None  # cases 存储多层嵌套的 ELIF，else_case 存储 ELSE

        if self.current_tok.matches(TT_KEYWORD, 'ELIF'):
            all_cases = res.register(self.if_expr_b())
            if res.error:
                return res
            cases, else_case = all_cases
        else:
            else_case = res.register(self.if_expr_c())
            if res.error:
                return res

        return res.success((cases, else_case))

    def if_expr_cases(self, case_keyword):
        res = ParseResult()
        cases = []
        else_case = None

        if not self.current_tok.matches(TT_KEYWORD, case_keyword):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '{case_keyword}'"
            ))

        res.register_advancement()  # 不要忘记记录当前正在读取的位置
        self.advance()

        condition = res.register(self.expr())
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'THEN'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            statements = res.register(self.statements())
            if res.error:
                return res
            cases.append((condition, statements, True))  # 往列表 cases 中添加元素

            if self.current_tok.matches(TT_KEYWORD, 'END'):
                res.register_advancement()
                self.advance()
            else:
                all_cases = res.register(self.if_expr_b_or_c())
                if res.error:
                    return res
                new_cases, else_case = all_cases
                cases.extend(new_cases)
        else:
            expr = res.register(self.statement())
            if res.error:
                return res
            cases.append((condition, expr, False))

            all_cases = res.register(self.if_expr_b_or_c())
            if res.error:
                return res
            new_cases, else_case = all_cases
            cases.extend(new_cases)

        return res.success((cases, else_case))

    # 语法设计： 简化程序的逻辑，流水式匹配、判断即可
    # for-expr  ->  KEYWORD:FOR IDENTIFIER EQ expr KEYWORD:TO expr
    #               (KEYWORD:STEP expr)? KEYWORD:THEN
    #               statement
    #           |   (NEWLINE statements KEYWORD:END)
    def for_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, 'FOR'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'FOR'"
            ))

        res.register_advancement()  # 套路操作，无论何时都不用忘记记录当前正在读取的位置，便于进程的回滚
        self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected identifier"
            ))

        var_name = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.type != TT_EQ:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '='"
            ))

        res.register_advancement()
        self.advance()

        # 1 TO 10，start_value = 1，end_value = 10
        start_value = res.register(self.expr())
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'TO'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'TO'"
            ))

        res.register_advancement()
        self.advance()

        end_value = res.register(self.expr())
        if res.error:
            return res

        if self.current_tok.matches(TT_KEYWORD, 'STEP'):
            res.register_advancement()
            self.advance()

            step_value = res.register(self.expr())
            if res.error:
                return res
        # 若没有设置 STEP 关键字
        else:
            step_value = None

        if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'THEN'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())
            if res.error:
                return res

            if not self.current_tok.matches(TT_KEYWORD, 'END'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected 'END'"
                ))

            res.register_advancement()
            self.advance()

            return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))

        body = res.register(self.statement())
        if res.error:
            return res

        return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))

    # while-expr  ->  KEYWORD:WHILE expr KEYWORD:THEN
    #                 statement
    #             |   (NEWLINE statements KEYWORD:END)
    def while_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, 'WHILE'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'WHILE'"
            ))

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'THEN'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'THEN'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())  # 结果值
            if res.error:
                return res

            if not self.current_tok.matches(TT_KEYWORD, 'END'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected 'END'"
                ))

            res.register_advancement()
            self.advance()

            return res.success(WhileNode(condition, body, True))

        body = res.register(self.statement())
        if res.error:
            return res

        return res.success(WhileNode(condition, body, False))

    # func-def  ->  KEYWORD:FUN IDENTIFIER?
    #               LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN
    #               (ARROW expr)
    #           |   (NEWLINE statements KEYWORD:END)

    def func_def(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, 'FUN'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'FUN'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_IDENTIFIER:
            var_name_tok = self.current_tok
            res.register_advancement()
            self.advance()
            if self.current_tok.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected '('"
                ))
        else:
            var_name_tok = None
            if self.current_tok.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected identifier or '('"
                ))

        res.register_advancement()
        self.advance()
        arg_name_toks = []

        if self.current_tok.type == TT_IDENTIFIER:
            arg_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()

            while self.current_tok.type == TT_COMMA:
                res.register_advancement()
                self.advance()

                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        f"Expected identifier"
                    ))

                arg_name_toks.append(self.current_tok)
                res.register_advancement()
                self.advance()

            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected ',' or ')'"
                ))
        else:
            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected identifier or ')'"
                ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_ARROW:
            res.register_advancement()
            self.advance()

            body = res.register(self.expr())
            if res.error:
                return res

            return res.success(FuncDefNode(
                var_name_tok,
                arg_name_toks,
                body,
                True
            ))

        if self.current_tok.type != TT_NEWLINE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '->' or NEWLINE"
            ))

        res.register_advancement()
        self.advance()

        body = res.register(self.statements())
        if res.error:
            return res

        if not self.current_tok.matches(TT_KEYWORD, 'END'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'END'"
            ))

        res.register_advancement()
        self.advance()

        return res.success(FuncDefNode(
            var_name_tok,
            arg_name_toks,
            body,
            False
        ))

    ###################################

    # 抽离文法中 func_a op func_b 类似的公共操作，比如 factor ((MUL|DIV) factor)*
    # 构建 AST
    def bin_op(self, func_a, ops, func_b=None):
        # func_b 形参类型是函数且为可选参数
        if func_b == None:
            func_b = func_a

        res = ParseResult()
        left = res.register(func_a())
        if res.error:
            return res

        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
            # 因为此时该方法调用的其它函数已经调用 advance 函数完成向前读取的功能，所以当前 token 为 op_token
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)


#######################################
# IMPORTS
#######################################

from util.parser_result import ParseResult
from util.error import InvalidSyntaxError
from data.tokens import *
from util.nodes import *
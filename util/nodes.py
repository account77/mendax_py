#######################################
# NODES
# 抽象语法树（AST）的结点
#######################################

# 准备一个抽象语法树的 FOR WHILE 等的结点图示

# 数字结点
class NumberNode:
    def __init__(self, tok):
        self.tok = tok  # 把形参的值装入到自己的“布兜”里

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'


# 字符串结点
class StringNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self):
        return f'{self.tok}'


# 列表结点
class ListNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes  # 列表中的元素

        self.pos_start = pos_start
        self.pos_end = pos_end


# 获取指定变量名的值的结点 （访问变量）
class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end


# 为指定变量名分配值的结点 （变量赋值）
class VarAssignNode:
    def __init__(self, var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.value_node.pos_end


# 二元操作结点 （加｜减｜乘｜除）  1 + 2: left_node = '1' op_tok = '+' right_node = '2'
class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'


# 一元操作结点 （-1）  -1: op_tok = '-' node = '1'
class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node

        self.pos_start = self.op_tok.pos_start
        self.pos_end = node.pos_end

    def __repr__(self):
        return f'({self.op_tok}, {self.node})'


# 关键字 IF 的结点
class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case

        # self.cases[0][0] 表示起始IF的第1个表达式；cases 里面装的本来就是 expr
        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (
            self.else_case or self.cases[len(self.cases) - 1])[0].pos_end  # 要么是最后 ELSE 的表达式，要么是 ELIF 的最后 1 个表达式


# 关键字 FOR 的结点
class ForNode:
    def __init__(self, var_name_tok, start_value_node, end_value_node, step_value_node, body_node, should_return_null):
        self.var_name_tok = var_name_tok
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.body_node.pos_end


# 关键字 WHILE 的结点
class WhileNode:
    def __init__(self, condition_node, body_node, should_return_null):
        self.condition_node = condition_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end


# 函数定义的结点
class FuncDefNode:
    def __init__(self, var_name_tok, arg_name_toks, body_node, should_auto_return):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node
        self.should_auto_return = should_auto_return

        if self.var_name_tok:
            self.pos_start = self.var_name_tok.pos_start
        elif len(self.arg_name_toks) > 0:
            self.pos_start = self.arg_name_toks[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end


# 函数调用的结点
class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        # add(1,2) node_to_call -> add, arg_nodes -> 1,2
        self.node_to_call = node_to_call  # 被调用的函数
        self.arg_nodes = arg_nodes  # 被调用的参数

        self.pos_start = self.node_to_call.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end


# 关键字 RETURN 的结点
class ReturnNode:
    def __init__(self, node_to_return, pos_start, pos_end):
        self.node_to_return = node_to_return

        self.pos_start = pos_start
        self.pos_end = pos_end


# 关键字 CONTINUE 的结点
class ContinueNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end


# 关键字 BREAK 的结点
class BreakNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

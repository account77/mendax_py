#######################################
# INTERPRETER
# 解释器，粗略的讲，就是依据抽象语法树来计算结果
#######################################


class Interpreter:
    def visit(self, node, context):  # node : ASTNode，起始结点；context : 默认上下文
        # type(node) 获取当前结点的实例，__name__ 获取类实例的名称，比如 NumberNode etc. 然后通过 visit_ 进行字符串拼接
        method_name = f'visit_{type(node).__name__}'
        # 获取类实例的属性值(method_name)
        method = getattr(self, method_name, self.no_visit_method)
        # 根据 method_name 执行相应的方法，比如 visit_NumberNode
        return method(node, context)

    # 若依据 method_name 没有取到值，则会调用该默认方法
    def no_visit_method(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    ###################################

    def visit_NumberNode(self, node, context):
        return RTResult().success(
            Number(node.tok.value).set_context(
                context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_StringNode(self, node, context):
        return RTResult().success(
            String(node.tok.value).set_context(
                context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ListNode(self, node, context):
        res = RTResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.should_return():
                return res

        return res.success(
            List(elements).set_context(context).set_pos(
                node.pos_start, node.pos_end)
        )

    # 实现解释器的变量访问的操作
    def visit_VarAccessNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = context.symbol_table.get(var_name)  # 从符号表中取值

        # 访问变量失败
        if not value:
            return res.failure(RTError(
                node.pos_start, node.pos_end,
                f"'{var_name}' is not defined",
                context
            ))

        # 从另一个角度来说，python 是一门引用性的语言，传递该变量后再被修改，就会影响到“母体”
        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(value)

    # 实现解释器的变量赋值的操作
    def visit_VarAssignNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_tok.value
        # 此处含有递归操作，取得一个具体的结果，比如 -1
        value = res.register(self.visit(node.value_node, context))
        if res.should_return():
            return res

        context.symbol_table.set(var_name, value)
        return res.success(value)

    # 实现解释器的二元操作部分（不要忘记字符串的拼接..）
    def visit_BinOpNode(self, node, context):
        res = RTResult()
        # 递归处理 AST 左结点，使用 register 方法是由于中途存在报错的可能性
        left = res.register(self.visit(node.left_node, context))
        if res.should_return():
            return res
        right = res.register(self.visit(
            node.right_node, context))  # 递归处理 AST右结点
        if res.should_return():
            return res

        # 调用四则运算等所对应的函数来计算结果，比如 Number 类 和 String 类
        if node.op_tok.type == TT_PLUS:
            # return Number(self.value + other.value).set_context(self.context), None
            result, error = left.added_to(right)
        elif node.op_tok.type == TT_MINUS:
            result, error = left.subbed_by(right)
        elif node.op_tok.type == TT_MUL:
            result, error = left.multed_by(right)
        elif node.op_tok.type == TT_DIV:
            result, error = left.dived_by(right)
        elif node.op_tok.type == TT_POW:
            result, error = left.powed_by(right)
        elif node.op_tok.type == TT_EE:
            result, error = left.get_comparison_eq(right)
        elif node.op_tok.type == TT_NE:
            result, error = left.get_comparison_ne(right)
        elif node.op_tok.type == TT_LT:
            result, error = left.get_comparison_lt(right)
        elif node.op_tok.type == TT_GT:
            result, error = left.get_comparison_gt(right)
        elif node.op_tok.type == TT_LTE:
            result, error = left.get_comparison_lte(right)
        elif node.op_tok.type == TT_GTE:
            result, error = left.get_comparison_gte(right)
        elif node.op_tok.matches(TT_KEYWORD, 'AND'):
            result, error = left.anded_by(right)
        elif node.op_tok.matches(TT_KEYWORD, 'OR'):
            result, error = left.ored_by(right)

        if error:
            return res.failure(error)
        else:
            # set_pos Value 类
            return res.success(result.set_pos(node.pos_start, node.pos_end))

    # 实现解释器的一元操作部分
    def visit_UnaryOpNode(self, node, context):
        res = RTResult()
        number = res.register(self.visit(node.node, context))
        if res.should_return():
            return res

        # python 中的变量不需要声明，每个变量在使用前都必须赋值，变量赋值以后该变量才会被创建
        # 在 python 中，变量就是变量，它没有类型，我们所说的”类型”是变量所指的内存中对象的类型
        error = None

        if node.op_tok.type == TT_MINUS:
            number, error = number.multed_by(Number(-1))
        elif node.op_tok.matches(TT_KEYWORD, 'NOT'):
            number, error = number.notted()

        if error:
            return res.failure(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))

    # 实现解释器的 IF 条件表达式部分
    def visit_IfNode(self, node, context):
        res = RTResult()

        for condition, expr, should_return_null in node.cases:
            if res.should_return():
                # 条件本身也是一个表达式，放入 self.visit 函数中，取得具体的结果
                condition_value = res.register(self.visit(condition, context))
            return res

            # 条件为真，则可以执行 THEN 后面的 expr
            if condition_value.is_true():
                expr_value = res.register(
                    self.visit(expr, context))  # 执行表达式，获得所对应的值
                if res.should_return():
                    return res
                return res.success(Number.null if should_return_null else expr_value)

        # ELSE 后面的 expr
        if node.else_case:
            expr, should_return_null = node.else_case
            expr_value = res.register(
                self.visit(expr, context))  # 执行表达式，获得所对应的值
            if res.should_return():
                return res
            return res.success(Number.null if should_return_null else expr_value)

        return res.success(Number.null)

    # 实现解释器的 FOR 循环部分
    def visit_ForNode(self, node, context):
        res = RTResult()
        elements = []

        start_value = res.register(self.visit(node.start_value_node, context))
        if res.should_return():
            return res

        end_value = res.register(self.visit(node.end_value_node, context))
        if res.should_return():
            return res

        if node.step_value_node:
            step_value = res.register(
                self.visit(node.step_value_node, context))
            if res.should_return():
                return res
        else:
            step_value = Number(1)

        i = start_value.value

        # 若设置的 STEP 值大于 0，则从小到大累加
        if step_value.value >= 0:
            def condition():
                return i < end_value.value
        else:
            def condition():
                return i > end_value.value

        while condition():
            # FOR 循环中的变量名存入符号表，保证其值在循环中可被直接使用，循环结束后亦可以被使用 （符号表如何区分全局变量和局部变量？）
            context.symbol_table.set(
                node.var_name_tok.value, Number(i))  # FOR i = 1 TO 3 中的 i
            i += step_value.value

            value = res.register(self.visit(node.body_node, context))
            if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False:
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            elements.append(value)

        return res.success(
            Number.null if node.should_return_null else
            List(elements).set_context(context).set_pos(
                node.pos_start, node.pos_end)
        )

    # 实现解释器的 WHILE 循环部分
    def visit_WhileNode(self, node, context):
        res = RTResult()
        elements = []

        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.should_return():
                return res

            if not condition.is_true():
                break

            value = res.register(self.visit(node.body_node, context))
            if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False:
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            elements.append(value)

        return res.success(
            Number.null if node.should_return_null else
            List(elements).set_context(context).set_pos(
                node.pos_start, node.pos_end)
        )

    # 实现解释器的函数定义部分，获得函数的可调用对象
    def visit_FuncDefNode(self, node, context):
        res = RTResult()

        # 若 node.var_name_tok.value 存在则罢了，否则为匿名函数
        func_name = node.var_name_tok.value if node.var_name_tok else None
        body_node = node.body_node
        # for arg_name in node.arg_name.toks then [NO.1, NO.2, NO.3...] = arg_name.value
        arg_names = [arg_name.value for arg_name in node.arg_name_toks]
        func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(
            context).set_pos(node.pos_start, node.pos_end)  # pos 方便对报错位置的定位

        # 若不是匿名函数，则存入符号表（func_name -- func_value）；func_value 函数可调用对象
        if node.var_name_tok:
            context.symbol_table.set(func_name, func_value)

        # 匿名函数
        return res.success(func_value)

    # 实现解释器的函数调用部分，依据 func_name 从符号表中取 func_value
    def visit_CallNode(self, node, context):
        res = RTResult()
        args = []

        # 递归过程，最终会调用 visit_VarAccessNode 函数通过函数名从符号表中取值，也就是可调用函数对象
        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.should_return():
            return res
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        # 形参若为表达式（1+2），对其作求值处理
        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.should_return():
                return res

        return_value = res.register(value_to_call.execute(args))
        if res.should_return():
            return res
        return_value = return_value.copy().set_pos(
            node.pos_start, node.pos_end).set_context(context)
        return res.success(return_value)

    # 实现解释器的 RETURN 关键字部分
    def visit_ReturnNode(self, node, context):
        res = RTResult()

        if node.node_to_return:
            value = res.register(self.visit(node.node_to_return, context))
            if res.should_return():
                return res
        else:
            value = Number.null

        return res.success_return(value)

    # 实现解释器的 CONTINUE 关键字部分
    def visit_ContinueNode(self, node, context):
        return RTResult().success_continue()

    # 实现解释器的 BREAK 关键字部分
    def visit_BreakNode(self, node, context):
        return RTResult().success_break()


#######################################
# IMPORTS
#######################################

from util.rt_result import RTResult
from util.values import Number, String, List, Function
from util.error import RTError
from data.tokens import *
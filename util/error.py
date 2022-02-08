from util.strings_with_arrows import string_with_arrows


class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        # self: 对象自身
        self.pos_start = pos_start  # 起始位置
        self.pos_end = pos_end  # 结束位置
        self.error_name = error_name  # 错误名称
        self.details = details  # 错误内容

    # 简化终端窗口的输出
    def as_string(self):
        result = f'{self.error_name}: {self.details}\n'
        # 提示报错文件的名称和报错位置（行号）
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        result += '\n\n' + \
            string_with_arrows(self.pos_start.ftxt,
                               self.pos_start, self.pos_end)
        return result


# 非法字符错误
class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)


# 预期字符错误
class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Expected Character', details)


# 无效语法错误
class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)


class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        self.context = context

    # 重写父类的 as_string 方法
    def as_string(self):
        result = self.generate_traceback()
        result += f'{self.error_name}: {self.details}'
        result += '\n\n' + \
            string_with_arrows(self.pos_start.ftxt,
                               self.pos_start, self.pos_end)
        return result

    # 生成错误栈信息
    def generate_traceback(self):
        result = ''
        pos = self.pos_start
        ctx = self.context

        # context 可能存在父级，所以需要通过 while 递归打印
        while ctx:
            result = f'  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return 'Traceback (most recent call last):\n' + result

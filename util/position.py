class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx  # 索引
        self.ln = ln  # 行
        self.col = col  # 列
        self.fn = fn  # 文件名称
        self.ftxt = ftxt

    # 往前读取
    def advance(self, current_char=None):
        self.idx += 1  # 增加索引
        self.col += 1  # 增加列号

        # 若遇到换行符
        if current_char == '\n':
            self.ln += 1  # 增加行号
            self.col = 0  # 列号归零

        return self  # 返回对象自身

    # 避免 python 引用性调用带来的问题（位置等）
    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

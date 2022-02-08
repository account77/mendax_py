class ParseResult:
    def __init__(self):
        self.error = None  # error 初始化为 None
        self.node = None  # node 初始化为 None
        self.last_registered_advance_count = 0
        self.advance_count = 0  # 当前正在读取的位置
        self.to_reverse_count = 0

    # 读取时，若发生错误，便于读取进程的回滚
    def register_advancement(self):
        self.last_registered_advance_count = 1  # 含义 ？
        self.advance_count += 1  # 当前正在读取的位置 +1

    # 存储解析的结果
    def register(self, res):
        self.last_registered_advance_count = res.advance_count
        self.advance_count += res.advance_count
        # 若在语法解析的中途报错，即没能解析到最后，而在中途报错
        if res.error:
            self.error = res.error
        return res.node  # 注意返回的是 node

    def try_register(self, res):
        if res.error:
            self.to_reverse_count = res.advance_count
            return None
        return self.register(res)

    # 若语法解析成功，此时会传入 node
    def success(self, node):
        self.node = node
        return self

    # 若语法解析失败，此时会传入 error
    def failure(self, error):
        if not self.error or self.last_registered_advance_count == 0:
            self.error = error
        return self

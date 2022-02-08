# 用于维持变量的值并在合适的时机将其回收；全局变量和局部变量（方法）具有各自的符号表；字典: key-value
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}  # 字典是另一种可变容器模型，且可存储任意类型对象
        self.parent = parent  # 父亲符号表，可用于判断作用域

    def get(self, name):
        value = self.symbols.get(name, None)  # 字典.get(key) --> value
        # 若该符号表查找失败，则尝试往父级符号表中去查找
        # 比如，于某个函数体内找不到变量 V，则可以在全局中查找到该变量 V
        if value == None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value):
        self.symbols[name] = value  # key-value 设置 vlaue

    def remove(self, name):
        del self.symbols[name]

class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent  # 上层
        self.parent_entry_pos = parent_entry_pos  # 上层的位置；调用链
        self.symbol_table = None

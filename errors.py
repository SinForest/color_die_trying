

class DimensionError(Exception):
    def __init__(self, text):
        super().__init__(text)

class NestedTestError(Exception):
    def __init__(self, name, e):
        super().__init__("Failed at: {}\nOrig. Error [{}]:\n{}".format(name, type(e), e))

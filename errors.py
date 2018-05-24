

class DimensionError(Exception):
    def __init__(self, text):
        super().__init__(text)

class NestedTestError(Exception):
    def __init__(self, name, e):
        super().__init__("Failed at: " + str(name) + "\nOrig. Error:\n" + str(e))

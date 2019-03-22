

class DimensionError(Exception):
    def __init__(self, text):
        super().__init__(text)

class NestedTestError(Exception):
    def __init__(self, name, e):
        super().__init__("Failed at: {}\nOrig. Error [{}]:\n{}".format(name, type(e), e))

class FieldError(Exception):
    def __init__(self, name):
        super().__init__(name)

class TurnError(Exception):
    def __init__(self, name):
        super().__init__(name)

class GameError(Exception):
    def __init__(self, name):
        super().__init__(name)

class TokenError(Exception):  #TODO: use more!
    def __init__(self, name):
        super().__init__(name)

class ServerLogicError(Exception):
    def __init__(self, name):
        super().__init__(name)

class ServerConnectionError(Exception):
    def __init__(self, name):
        super().__init__(name)

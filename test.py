from errors import *

import itertools

class Tests:
    def __init__(self):
        self.field_cases = {}

    def add_case_field(self, before, position, color, after, name=None):
        if name is None:
            for i,e in enumerate(sorted([x for x in self.field_cases.keys() if type(x) == int])):
                if i != e:
                    name = i
                    break
        while name in self.field_cases.keys():
            name = str(name) + "|"
        if {len(x) for x in before} != 1:
            raise DimensionError("invalid string dimensions in `before`")
        if {len(x) for x in after} != 1:
            raise DimensionError("invalid string dimensions in `after`")
        

from errors import *
from field import Field
import json

import itertools

class Tests:
    def __init__(self):
        self.field_cases = {}
    
    def test_func_err(self, name, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise NestedTestError(name, e)
    
    def test_assert_equal(self, name, real, should):
        try:
            assert real == should, "\n".join(["{} <-r-s->  {}".format(
                                   "".join(r),"".join(s))
                                   for r, s in zip(real, should)])
        except Exception as e:
            raise NestedTestError(name, e)

    
    def test_defaults(self):
        s = ""
        try:
            s = "[init] creating 20x20-field"
            field = Field(20)
            s = "[play] playing card on (0,0)"
            field.play_card(0, 0, "r")
            s = "[fill] playing card on (0,19)"
            field.play_card(0, 19, "r")
            s = "[mix] playing card on (19,19)"
            field.play_card(19, 19, "y")
            s = "[get] get mixed color on (9,19)"
            color = field.get_color(9, 19)
            s = "[check] color should be orange"
            assert color == "o"
            s = "[get] get mixed color on (0,9)"
            color = field.get_color(0, 9)
            s = "[check] color should be red"
            assert color == "r"
        except Exception as e:
            print("Default Tests failed at:\n" + s)
            print("Field:\n" + str(field))
            raise e


    def add_case_field(self, before, position, color, after, name=None):
        if name is None:
            for i,e in enumerate(sorted([x for x in self.field_cases.keys() if type(x) == int])):
                if i != e:
                    name = i
                    break
        while name in self.field_cases.keys():
            name = str(name) + "|"
        self.field_cases[name] = ([list(s) for s in before], tuple(position), color, [list(s) for s in after])
    
    def field_test(self, name):
        (b, p, c, a) = self.field_cases[name]
        field = self.test_func_err("Creating Field", Field, field=b)
        self.test_func_err("Setting Color", field.play_card, *p, c)
        self.test_assert_equal("Testing equality", field._data, a)
        

    def print_passed(self, name, fail, amount):
        s = "{}/{}".format(amount - fail, amount) if fail else "all"
        print("{} Tests: {} tests passed.".format(name, s))


    def test(self, verbose=True):
        failed = {}
        # test default cases:
        self.test_defaults() # Doesn't continue if this fails!
        print("Default Tests passed")
        # test field tests:
        fail_count = 0
        for name in sorted(self.field_cases.keys()):
            try:
                self.field_test(name)
            except NestedTestError as e:
                fail_count += 1
                failed[name] = e
        self.print_passed("Field", fail_count, len(self.field_cases))
        if fail_count > 0:
            for name, e in failed.items():
                print('"{}": '.format(name), e)
    
    def read_field_cases(self, fp="./field_tests.json"):
        for name, case in json.load(open(fp, 'r')).items():
            self.add_case_field(**case, name=name)
        return self

def main():
    tests = Tests().read_field_cases()
    tests.test()

if __name__ == '__main__':
    main()
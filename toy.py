#!/bin/env python

c_base = ["r", "y", "b"]
c_secu = ["o", "g", "p"]
c_illu = ["w", "k"]
colors = c_base + c_secu + c_illu
MIX    = {"rr":"r", "bb":"b", "yy":"y",
          "rb":"p", "by":"g", "yr":"o",
          "br":"p", "yb":"g", "ry":"o"}
UNMIX  = {"p":["b", "r"],"g":["y", "b"],"o":["r", "y"]}
dirs   = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def mix_colors(c1, c2):
    if c1 not in c_base or c2 not in c_base:
        raise ValueError("Invalid Colors '{}', '{}' for mixing".format(c1, c2))
    return MIX[c1+c2]

def unmix_color(c, rev=False):
    if c not in c_secu:
        raise ValueError("Invalid Color '{}' for unmixing".format(c))
    return [x for x in c_base if x not in UNMIX[c]] if rev else UNMIX[c]


class Field:
    def __init__(self, size):
        self.size = size
        self._data = ["x" * size] * size # init empty field
        # _data[i]: i-th row (= string)
    
    def vc(self, *args): # valid
        """
        tests an arbitrary number of numbers
        for being positive and smaller self.size
        """
        for z in args:
            if not (0 <= z < self.size):
                return False
        return True

    def set_color(self, x, y, c):
        if c in colors:
            if self.vc(x, y) and (self._data[y][x] == "x" or c == "x"):
                self._data[y][x] = c 
            else:
                raise RuntimeError("Invalid Coordinates ({}, {})".format(x, y))
        else:
            raise ValueError("Invalid Color '{}'".format(c))
    
    def can_set_color(self, x, y, c):
        return c in colors and self.vc(x, y) and self.get_color(x, y) == "x"
    
    def get_color(self, x, y):
        return self._data[y][x]
    
    def play_card(self, x, y, c):
        if not self.can_set_color(x, y, c):
            raise RuntimeError("Invalid Move!")
        if c in c_base:
            self.proc_base(x, y, c)
        elif c in c_secu:
            self.proc_secu(x, y, c)
        elif c in c_illu:
            self.proc_illu(x, y, c)
        else:
            raise ValueError("Invalid Color '{}' in 'play_card'".format(c))
    
    def fill(self, x0, y0, x1, y1, c):
        if not self.vc(x0, y0, x1, y1):
            raise RuntimeError("Invalid Coordinates in 'fill'")
        if x0 == x1:
            for yi in range(min(y0, y1), max(y0, y1) + 1):
                self.set_color(x0, yi, c)
        elif y0 == y1:
            for xi in range(min(x0, x1), max(x0, x1) + 1):
                self.set_color(xi, y0, c)
        else:
            raise RuntimeError("Invalid Coordinates in 'fill'")
    
    def proc_base(self, x, y, c):
        center_colors = set()
        for d in dirs:
            dx, dy = d     # direction deltas
            cx, cy = x+dx, y+dy  # start curr. postition next to start position
            trav_secu = set()
            while self.vc(cx, cy): # walk into direction
                this_color = self.get_color(cx, cy)
                if this_color == "x":
                    continue
                if this_color in c_base:
                    c_fill = mix_colors(this_color, c)
                    # only overpaint res. color when mixing
                    if c_fill == c or len(trav_secu - {c}) == 0:
                        self.fill(x, y, cx, cy, c_fill)
                        center_colors.add(c_fill)
                    break
                if this_color in c_secu:
                    trav_secu.add(c)
                    if c in unmix_color(this_color, rev=True):
                        break# on color that can't be mixed with `c`
                cx, cy = cx+dx, cy+dy # step
        
        if len(center_colors) != 1: # if unclear about center color (or nothing
            self.set_color(x, y, c) # filled), leave played color on field
    
    def proc_secu(self, x, y, c):
        center_colors = set()
        unmix = unmix_color(c)
        for d in dirs:
            dx, dy = d           # direction deltas
            cx, cy = x+dx, y+dy  # start curr. postition next to start position
            trav_base = set()
            while self.vc(cx, cy): # walk into direction
                this_color = self.get_color(cx, cy)
                if this_color == "x":
                    continue
                if this_color in c_base:
                    if c in unmix:
                        trav_base.add(this_color)
                        if len(trav_base) > 1:
                            break # can't overpaint more then one base color
                    else:
                        break # can't ovepaint non-used base color
                cx, cy = cx+dx, cy+dy # step

                if this_color == c:
                    self.fill(x, y, cx, cy, c)
                    center_colors.add(c)

        if len(center_colors) != 1: # if unclear about center color (or nothing
            self.set_color(x, y, c) # filled), leave played color on field

    def proc_illu(self, x, y, c):
        center_colors = set()
        unmix = unmix_color(c)
        for d in dirs:
            dx, dy = d           # direction deltas
            cx, cy = x+dx, y+dy  # start curr. postition next to start position
            while self.vc(cx, cy): # walk into direction
                this_color = self.get_color(cx, cy)
                if this_color == "x":
                    continue
                if this_color in c_illu:
                    if this_color == c:
                        self.fill(x, y, cx, cy, c)
                        center_colors.add(c)
                        break
                    else:
                        self.fill(x, y, cx, cy, "x")
                        center_colors.add("x")
                        break
                cx, cy = cx+dx, cy+dy # step
            
        if len(center_colors) != 1: # if unclear about center color (or nothing
            self.set_color(x, y, c) # filled), leave played color on field
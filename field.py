#!/bin/env python

from const import *
from errors import *
from helper import mix_colors, unmix_color

class Field:
    def __init__(self, size=-1, field=None):
        self.size = size
        if field:
            if len({len(x) for x in field}) != 1:
                raise DimensionError("invalid string dimensions in `field`")
            elif size >= 0 and len(field[0]) != size:
                raise DimensionError("`size` not matching dimension of `field`")
            else:
                self._data = field
                self.size  = len(field[0])
        else:
            if size < 0:
                raise ValueError("`size` < 0 only allowed with field given")
            else:
                self._data = [["x"] * size for __ in range(size)]# init empty field
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
        if c in COLORS or c == "x":
            if self.vc(x, y):
                self._data[y][x] = c #WUT!? # I can't remember why I wrote 'WUT!?' here?
            else:
                raise RuntimeError("Invalid Coordinates ({}, {})".format(x, y))
        else:
            raise ValueError("Invalid Color '{}' in 'set_color'".format(c))

    def can_set_color(self, x, y, c):
        return c in COLORS and self.vc(x, y) and self.get_color(x, y) == "x"
        # "x" is not allowed here, since this checks for a playable move

    def get_color(self, x, y):
        return self._data[y][x]
    
    def play_card(self, x, y, c):
        if not self.can_set_color(x, y, c):
            raise FieldError("Invalid Move '{}' on '{}' at ({}/{})!"
                               .format(c, self.get_color(x, y), x, y))
        if c in C_BASE:
            self.proc_BASE(x, y, c)
        elif c in C_SECU:
            self.proc_SECU(x, y, c)
        elif c in C_ILLU:
            self.proc_ILLU(x, y, c)
        else:
            raise ValueError("Invalid Color '{}' in 'play_card'".format(c))
    
    def fill(self, x0, y0, x1, y1, c):
        if not self.vc(x0, y0, x1, y1):
            raise RuntimeError("Invalid Coordinates in 'fill' [({}/{}), ({}/{})] on size '{}'".format(x0,y0,x1,y1,self.size))
        if x0 == x1:
            for yi in range(min(y0, y1), max(y0, y1) + 1):
                self.set_color(x0, yi, c)
        elif y0 == y1:
            for xi in range(min(x0, x1), max(x0, x1) + 1):
                self.set_color(xi, y0, c)
        else:
            raise RuntimeError("Coordinates in 'fill' not on line [({}/{}), ({}/{})]".format(x0,y0,x1,y1))
    
    def proc_BASE(self, x, y, c):
        center_colors = set()
        for d in DIRS:
            dx, dy = d     # direction deltas
            cx, cy = x+dx, y+dy  # start curr. postition next to start position
            trav_secu = set()
            while self.vc(cx, cy): # walk into direction
                this_color = self.get_color(cx, cy)
                if this_color in C_BASE:
                    c_fill = mix_colors(this_color, c)
                    # only overpaint res. color when mixing
                    if c_fill == c or len(trav_secu - {c_fill}) == 0:
                        self.fill(x, y, cx, cy, c_fill)
                        center_colors.add(c_fill)
                    break
                if this_color in C_SECU:
                    trav_secu.add(c)
                    if c in unmix_color(this_color, rev=True):
                        break# on color that can't be mixed with `c`
                cx, cy = cx+dx, cy+dy # step
        if len(center_colors) != 1: # if unclear about center color (or nothing
            self.set_color(x, y, c) # filled), leave played color on field
    
    def proc_SECU(self, x, y, c):
        center_colors = set()
        unmix = unmix_color(c)
        for d in DIRS:
            dx, dy = d           # direction deltas
            cx, cy = x+dx, y+dy  # start curr. position next to start position
            trav_base = set()
            while self.vc(cx, cy): # walk into direction
                this_color = self.get_color(cx, cy)
                if this_color in C_BASE:
                    if this_color in unmix:
                        trav_base.add(this_color)
                        if len(trav_base) > 1:
                            break # can't overpaint more then one base color
                    else:
                        break # can't overpaint non-used base color
                elif this_color in C_SECU:
                    if this_color == c:
                        self.fill(x, y, cx, cy, c)
                        center_colors.add(c)
                        break
                    else:
                        break

                cx, cy = cx+dx, cy+dy # step

        if len(center_colors) != 1: # if unclear about center color (or nothing
            self.set_color(x, y, c) # filled), leave played color on field

    def proc_ILLU(self, x, y, c):
        center_colors = set()
        for d in DIRS:
            dx, dy = d           # direction deltas
            cx, cy = x+dx, y+dy  # start curr. postition next to start position
            while self.vc(cx, cy): # walk into direction
                this_color = self.get_color(cx, cy)
                if this_color in C_ILLU:
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
    
    def number_tiles_used(self):
        return sum([1 for c in "".join(self._data) if c != "x"]) #TODO: write tests!
    
    def percentage_tiles_used(self):
        return self.number_tiles_used() / (self.size**2) * 100.

    def __str__(self):
        return "\n".join(["".join(x) for x in self._data])

    def __repr__(self):
        return "<Field with size `{}` at {}>".format(self.size, id(self))
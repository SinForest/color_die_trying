C_BASE = ["r", "y", "b"]
C_SECU = ["o", "g", "p"]
C_ILLU = ["w", "k"]
COLORS = C_BASE + C_SECU + C_ILLU
MIX    = {"rr":"r", "bb":"b", "yy":"y",
          "rb":"p", "by":"g", "yr":"o",
          "br":"p", "yb":"g", "ry":"o"}
UNMIX  = {"p":["b", "r"],"g":["y", "b"],"o":["r", "y"]}
DIRS   = [(-1, 0), (1, 0), (0, -1), (0, 1)]
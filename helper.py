from const import *

def mix_colors(c1, c2):
    if c1 not in C_BASE or c2 not in C_BASE:
        raise ValueError("Invalid colors '{}', '{}' for mixing".format(c1, c2))
    return MIX[c1+c2]

def unmix_color(c, rev=False):
    if c not in C_SECU:
        raise ValueError("Invalid Color '{}' for unmixing".format(c))
    return [x for x in C_BASE if x not in UNMIX[c]] if rev else UNMIX[c]
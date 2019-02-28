import random
import string
from collections import OrderedDict

from const import *
from errors import TurnError, GameError
from field import Field

MIN_HAND = 25
MAX_HAND = 35
MAX_PLAYERS = 10
CHARS = [c for c in string.ascii_letters + string.digits + string.punctuation if c not in {"'", '"', "\\"}]

class Player:

    def __init__(self, name, token):
        self.name = str(name)
        self.token = token
        self.cards = None
        ...
    
    def init_cards(self, size):
        self.cards = dict(zip(C_BASE+C_SECU, [size//5]*6), w=size//10, k=size//10)
    
    def dict(self):
        return self.__dict__


class Turn:

    def __init__(self, name, pos, col, token, **kwargs):
        self.name = name
        self.pos = pos
        self.col = col
        self.token = token

    def dict(self):
        return self.__dict__

class Game:

    def __init__(self, field_size=50, n_players=2):
        if not (0 < n_players < MAX_PLAYERS):
            raise ValueError("Can't play with {} players.".format(n_players))
        if field_size < 1:
            raise ValueError("Can't play with field of size {0}x{0}".format(field_size))
        self._started   = False
        self._n_players = n_players
        self._players   = {}  # dict of `Player` objects
        self._field     = Field(field_size)
        self._on_turn   = None
        self._turns     = []

    def __repr__(self):
        return "<Game [{}started, {} players, {} fieldsize] at {}>".format("" if self.has_started() else "not ", self._n_players if self.has_started() else "{}/{}".format(len(self._players), self._n_players), self._field.size, id(self))

    def reg_player(self, name):
        if self.has_started():
            raise GameError("Can't add player, game is already running.")
        if len(self._players) >= self._n_players:
            return None
        token = None
        while (token is None) or (token in self._players.keys()):
            token = "".join([random.choice(CHARS) for __ in range(random.randint(MIN_HAND, MAX_HAND))])
        player = Player(name, token)
        player.init_cards(self._field.size)
        self._players[token] = player
        return player
    
    def is_name_registered(self, name):
        return name in [p.name for p in self._players.values()]
    
    def is_token_registered(self, name):
        return name in self._players.keys()

    def start(self, force=False):
        if self.has_started():
            raise GameError("Can't start game, is already running.")
        if len(self._players) < 1:
            return False
        if force and len(self._players) < self._n_players: # force to start game with too few players
            self._n_players = len(self._players)
        if len(self._players) < self._n_players:
            return False
        self._turn_order = list(self._players.keys())
        random.shuffle(self._turn_order)
        self._on_turn = 0
        self.lay_starting_cards()
        self._started = True
        
        return True
    
    def lay_starting_cards(self):
        if self._started: return
        size = self._field.size
        offs = int(size/3)
        off2 = size - offs - 1
        for x, y in [(offs, offs), (off2, offs), (offs, off2), (off2, off2)]:
            self._field.set_color(x, y, random.choice(C_BASE + C_SECU))
        


    def log_turn(self, turn):
        self._turns.append(turn)
    
    def get_past_turn(self, n=1, private=True):
        if n > len(self._turns):
            return None
        turn = self._turns[-n]
        if private:
            turn.token = ""
        return turn
    
    def get_curr_player(self):
        return self._players[self.get_curr_player_token()]
    
    def get_player(self, token):
        try:
            return self._players[token]
        except KeyError:
            return None

    def get_curr_player_token(self):
        if self.has_started():
            return self._turn_order[self._on_turn]
        else:
            raise GameError("Can't get player, the game hasn't started yet!")
        
    def play(self, turn):
        if not self.has_started() == True:
            raise GameError("Can't play turn, the game hasn't started yet!")
        
        if type(turn) != Turn:
            raise TurnError("wrong type for `turn`")
        #TODO: check integrity of Turn-Object
        
        if turn.token not in self._players.keys() or self._players[turn.token].name != turn.name:
            raise TurnError("invalid name-token combination")
        
        if self.get_curr_player_token() != turn.token:
            raise TurnError("player '{}' is not on turn".format(turn.name))
        
        if not (type(turn.pos) == tuple and len(turn.pos) == 2 and self._field.vc(turn.pos)):
            raise TurnError("invalid position in `turn`")
        
        if turn.col not in COLORS:
            raise TurnError("invalid color in `turn`")
        
        if self._players[turn.token].cards[turn.col] < 1:
            raise TurnError("player '{}' has no '{}' left".format(turn.name, turn.col))
        
        # play turn
        self._field.play_card(*turn.pos, turn.col)
        self._players[turn.token].cards[turn.col] -= 1

        self.log_turn(turn)

    def has_started(self):
        return self._started
    
    def get_field(self, string=False):
        return str(self._field) if string else self._field

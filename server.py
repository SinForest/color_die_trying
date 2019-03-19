import socket
import json
from functools import reduce
import traceback
import sys

from game import Game, Turn
from errors import *
from game import CHARS

MAX_LENGTH = 99_999

class GameConnector:
    def __init__(self, debug=True):
        self.debug = debug
    
    def create_msg(self, d):
        js = json.dumps(d).encode("utf-8")
        return f"{len(js)}:".encode("utf-8") + js
    
    def invalid_msg(self, msg=None):
        err = {"type": "invalid"}
        if msg: err["mgs"] = msg
        if self.debug: print(f"### sending message ### \n{err}\n#######################")
        return self.create_msg(err)
    
    def reg_msg(self, name):
        res = {"type": "reg",
               "name": str(name)}
        if self.debug: print(f"### sending message ### \n{res}\n#######################")
        return self.create_msg(res)
    
    def start_msg(self, token, force=False):
        res = {"type": "start",
               "token": token}
        if force: res["force"] = "1"
        if self.debug: print(f"### sending message ### \n{res}\n#######################")
        return self.create_msg(res)
    
    def error_msg(self, errtype, msg=None):
        err = {"type"   : "error", 
               "errtype": str(errtype)}
        if msg: err["mgs"] = msg
        if self.debug: print(f"### sending message ### \n{err}\n#######################")
        return self.create_msg(err)
    
    def turn_msg(self, turn):
        res = {"type": "turn",
               "turn": turn.dict()}
        if self.debug: print(f"### sending message ### \n{res}\n#######################")
        return self.create_msg(res)

    def recv(self, conn, decode=True):
        """
        wrap this method in try/finally, to ensure closing of conn
        """
        alldata = b""
        exp_len = 0
        pre_len = 0
        while True:
            data = conn.recv(16)
            if self.debug: print(f"incoming data: {data}")
            alldata += data
            if not data:
                if self.debug: print("connection terminated")
                break
            if exp_len > 0:
                ...
            elif b":" in alldata:
                pre = alldata[:alldata.index(b":")]
                exp_len = int(pre)
                pre_len = len(pre) + 1
                if exp_len == 0:
                    if self.debug: print("empty message sent")
                    return None if decode else b""
            else:
                # in this case, only bytes before the colon are sent
                # must be castable into int (and not huge)
                try:
                    assert int(alldata) < MAX_LENGTH
                except:
                    if self.debug: print("invalid expected length sent")
                    return None if decode else b""
            
            if exp_len > 0 and len(alldata) >= exp_len + pre_len:
                if self.debug: print("message has expected length")
                break
                    
        
        alldata = alldata[pre_len:exp_len+pre_len]
        #TODO: find out, if one recv can contain content of 2 different sends
        #      if yes, this has to be concidered...
        if decode:
            try:
                return json.loads(alldata)
            except json.JSONDecodeError as e:
                return e
        else:
            return alldata

class GameServer(GameConnector):
    def __init__(self, bind_address=('localhost', 13337), max_conn=10, debug=True, n_players=2):
        super().__init__(debug)
        self.game = Game(field_size=20, n_players=n_players)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(bind_address)
        self.sock.listen(max_conn)
        self.conns = {}
    
    def __del__(self):
        """
        ENSURE with try/finally, that the instance will be deleted!!
        """
        if self.debug: print("Server closing..!")
        self.sock.close()
        try:
            for conn in self.conns.values():
                conn.close()
        except:
            pass # >;-)
    
    def is_valid_name(self, name):
        print("name: ", name)
        if len(name) < 3: return False # <3
        if len(name) > 20: return False 
        if self.game.is_name_registered(name): return False
        if not reduce(lambda x,y: x and y, [c in CHARS for c in name]): return False
        return True
    
    def pop_player_conn(self, token):
        if token in self.conns.keys():
            conn = self.conns[token]
            del self.conns[token]
            return conn
        else:
            return None

    def keep_player_conn(self, token, conn, override=False):
        if self.debug:
            print_cyan(f"#[KEEP] token: {token}, conns: {[key for key in self.conns.keys()]}")
        if token in self.conns.keys():
            if override:
                if self.conns[token] != conn:
                    self.conns[token].close()
                else:
                    return
            else:
                raise ServerLogicError("Can't register player connection. There is an open connection.")
        self.conns[token] = conn
    
    def game_msg(self, token, msgtype="state", no_turn=False):
        state = self.game.get_field(string=True)
        player = self.game.get_player(token)
        if not player:
            raise ServerLogicError("unregistered token")
        res = {"type": msgtype,
               "field": state,
               "player": player.dict(),
               "order": self.game.get_next_turn_order()
               }
        if not no_turn:
            turn = self.game.get_past_turn() #TODO: maybe catch exceptions here? (turn could be None)
            res["turn"] = turn.dict()
            del res["turn"]["token"]
        if self.debug: print(f"### sending message ### \n{res}\n#######################")
        return self.create_msg(res)
    
    def bulk_game_msg(self, msgtype="state", no_turn=False, kill_conns=False):
        msgs = {}
        for token in self.conns.keys():
            try:
                msgs[token] = self.game_msg(token, msgtype=msgtype, no_turn=no_turn)
            except ServerLogicError: # unregistered token
                tmp_conn = self.pop_player_conn(token)
                tmp_conn.close()
                del tmp_conn

        tmp_keys = list(self.conns.keys()) # Wo-Ar, since keys are popped dur. iteration
        for token in tmp_keys:
            try:
                conn = self.pop_player_conn(token)
                conn.sendall(msgs[token])
            except:
                raise ServerConnectionError("Connection failed when sending messages")
            finally:
                if kill_conns:
                    conn.close()
                else:
                    self.keep_player_conn(token, conn)

    def start_game(self, force=False):
        if not(self.game.start(force)):
            return False
        self.bulk_game_msg(msgtype='start_state', no_turn=True)
        return True

    def listen_for_turn(self):
        conn, addr = self.sock.accept()
        msg = self.recv(conn, decode=True)
        if not msg or type(msg) == json.JSONDecodeError:
            conn.sendall(self.invalid_msg())
        else:
            # decode json
            try:
                assert msg["type"] in {"turn", "reconn"} # More types here
            except:
                conn.sendall(self.error_msg("turn_mode", "Server currently only accepting turns."))
                return None
            if msg["type"] == "turn":
                """ # this is optional, since Game.play() checks this
                try:
                    assert msg["token"] == self.game.get_curr_player_token()
                except:
                    conn.sendall(self.error_msg("no_token", "No token given or it's not your turn!"))
                    return None
                """
                try:  # build turn object
                    turn = Turn(**msg["turn"])
                except Exception as e:
                    conn.sendall(self.error_msg("inv_turn", "No or invalid turn object handed in 'turn' message."))
                    if self.debug:
                        print(f"Failed with Exception: {e}")
                        traceback.print_exc()
                    return None
                try: # play turn
                    self.game.play(turn)
                except GameError:
                    conn.sendall(self.error_msg("wtf", "Game not started yet. Sorry, this should not be happening!"))
                    return None
                except TurnError as e:
                    conn.sendall(self.error_msg("turn_err", f"An error occured before playing turn: <{e}>"))
                    return None
                except FieldError as e:
                    conn.sendall(self.error_msg("turn_err", f"An error occured while playing turn: <{e}>"))
                    return None
                try: # send responses
                    self.keep_player_conn(turn.token, conn, override=True)
                    self.bulk_game_msg()
                except:
                    ...
                    raise RuntimeError("Failing of sent messages not implemented yet! CRASH! AHHHH..!")
                return turn
            #TODO: "reconn"



    def listen_register_block(self):
        conn, addr = self.sock.accept()
        msg = self.recv(conn, decode=True)
        if not msg or type(msg) == json.JSONDecodeError:
            conn.sendall(self.invalid_msg())
        else:
            # decode json
            try:
                assert msg["type"] in {"reg", "start"} # invalid if wrong or no type                    
            except:
                conn.sendall(self.error_msg("reg_mode","Server currently only accepting registers"))
                return None
            if msg["type"] == "reg":
                try:
                    player_name = msg["name"]
                    assert self.is_valid_name(player_name), "invalid name"
                except Exception as e:
                    if self.debug: print("failed with error: ", e)
                    conn.sendall(self.error_msg("inv_name", "No or invalid name given!"))
                    return None
                
                # register player
                try:
                    player = self.game.reg_player(player_name)
                except GameError:
                    # this should not happen in register mode!
                    conn.sendall(self.error_msg("wtf", "Game already started. Sorry, this should not be happening!"))
                    return None
                if not player:
                    conn.sendall(self.error_msg("game_full", "Game already full!"))
                    return None

                # send response
                resp = {"type"  : "reg",
                        "msg"   : "Player registered.",
                        "player": player.dict()}
                conn.sendall(self.create_msg(resp)) #TODO: own Connector method
                self.keep_player_conn(player.token, conn)
                return player
            elif msg["type"] == "start":
                force = "force" in msg and msg["force"] == "1"
                try:
                    token = msg["token"]
                    assert self.game.is_token_registered(token)
                except:
                    conn.sendall(self.error_msg("no_token", "Starting game needs a registered player token!"))
                    return None
                try:
                    self.keep_player_conn(token, conn, override=True)
                    could_start = self.start_game(force) #Game is started here!
                except GameError:
                    conn.sendall(self.error_msg("wtf", "Game already started. Sorry, this should not be happening!"))
                    return None
                except ServerConnectionError:
                    conn.sendall(self.error_msg("start_conn", "A connection terminated while starting the game. Game resetting."))
                    #TODO: reset game
                    return None
                if not could_start:
                    conn.sendall(self.error_msg("start", "Game could not be started. Wrong amount of players."))
                    return None
                """ # this does not make sense. the normal game start message should suffice
                # send response
                resp = {"type"  : "started",
                        "msg"   : "Game started."}
                conn.sendall(self.create_msg(resp))
                """
                return True                    
        
def print_cyan(m):
    print("\033[36;1m", m, "\033[0m")

SERVER_ADDRESS = ('localhost', 13337)
MAX_CONN = 1

if __name__ == "__main__":
    
    n_players = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    serv = GameServer(n_players=n_players)
    try:
        p = None
        while p != True:
            print("waiting for start [blocking]")
            p = serv.listen_register_block()
            print(f"returned: {p}")

        while True:
            print("waiting for turn [blocking]")
            t = serv.listen_for_turn()
            print(f"returned: {t}")
            
    finally:
        del serv
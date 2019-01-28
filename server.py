import socket
import json
from functools import reduce

from game import Game
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
        if decode:
            try:
                return json.loads(alldata)
            except json.JSONDecodeError as e:
                return e
        else:
            return alldata

class GameServer(GameConnector):
    def __init__(self, bind_address=('localhost', 13337), max_conn=10, debug=True):
        super().__init__(debug)
        self.game = Game(field_size=20, n_players=2)
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
        for conn in self.conns.values():
            conn.close()
    
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
        if token in self.conns.keys():
            if override:
                self.conns[token].close()
            else:
                raise ServerLogicError("Can't register player connection. There is an open connection.")
        self.conns[token] = conn

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
                    could_start = self.game.start(force)
                except GameError:
                    conn.sendall(self.error_msg("wtf", "Game already started. Sorry, this should not be happening!"))
                    return None
                if not could_start:
                    conn.sendall(self.error_msg("start", "Game could not be started. Wrong amount of players."))
                    return None
                # send response
                resp = {"type"  : "started",
                        "msg"   : "Game started."}
                conn.sendall(self.create_msg(resp)) #TODO: own Connector method
                return True                    
        
        
SERVER_ADDRESS = ('localhost', 13337)
MAX_CONN = 1

if __name__ == "__main__":
    serv = GameServer()
    try:
        while True:
            print("blocking")
            p = serv.listen_register_block()
            print(f"returned: {p}")
    finally:
        del serv
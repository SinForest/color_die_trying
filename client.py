import socket

from server import GameConnector
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor


SERVER_ADDRESS = ('localhost', 13337)
FAKE_ADDRESS = ('localhost', 14447)

players = {}
conr = GameConnector(debug=True)
pool = ThreadPoolExecutor(4)

def print_green(m):
    print("\033[32;1m", m, "\n<END>\033[0m")

def print_red(m):
    print("\033[31;1m", m, "\n<END>\033[0m")

def send_new(addr, token, msg):
    players[token].close()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    players[token] = sock
    sock.connect(addr)
    sock.send(msg)
    return sock

def gen_recv(conr, decode, printfunc=None):
    def tmp(conn):
        answ = conr.recv(conn, decode=decode)
        if printfunc:
            printfunc(answ)
        return answ
    return tmp

def ui():
    print("enter server address [localhost:13337]")
    addr = input("-> ")
    if addr == "":
        addr = SERVER_ADDRESS
    elif ":" in addr:
        addr = tuple(addr.split(":"))
    else:
        exit("Wrong Address!")
    
    print("players to register [2]")
    num_players = input("-> ")# L______________________v
    num_players = int(num_players) if num_players else 2
    for i in range(num_players):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(addr)
        m = conr.reg_msg(f"Player_{i+1}")
        print_green(m)
        sock.send(m)
        answ = conr.recv(sock, decode=True)
        print_red(answ)
        players[answ["player"]["token"]] = sock
    
    
    print("start game [f=force]")
    force = input("-> ") == "f"
    token = next(iter(players.keys()))
    m = conr.start_msg(token)
    print_green(m)
    conn = send_new(addr, token, m)

    # there is no direct answer in this version
    #answ = conr.recv(conn, decode=True)
    #print_red(answ)

    func = gen_recv(conr, False, print_red)
    answers = pool.map(func, players.values())

    """
    for conn in players.values():
        answ = conr.recv(conn, decode=False)
        print_red(answ)
    """

    #TODO:
    print("turn (player, x, y, col)")
    inp = input("-> ")
    inp = inp.split()
    

if __name__ == "__main__":
    try:
        ui()
        #TODO
    finally:
        for conn in players.values():
            try:
                conn.close()
            except:
                pass
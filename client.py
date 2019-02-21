import socket

from server import GameConnector


SERVER_ADDRESS = ('localhost', 13337)
FAKE_ADDRESS = ('localhost', 14447)

players = {}
conr = GameConnector(debug=False)

def print_green(m):
    print("\033[32;1m", m, "\033[0m")

def print_red(m):
    print("\033[31;1m", m, "\033[0m")


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
    token, conn = next(iter(players.items()))
    m = conr.start_msg(token)
    print_green(m)
    conn.send(m) #TODO: send over new conn!!
    answ = conr.recv(sock, decode=True)
    print_red(answ)

    



if __name__ == "__main__":
    try:
        ui()
        print(players)
        #TODO
    finally:
        for conn in players.values():
            conn.close()
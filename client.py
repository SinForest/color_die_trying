import socket

from server import GameConnector


SERVER_ADDRESS = ('localhost', 13337)
FAKE_ADDRESS = ('localhost', 14447)

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(SERVER_ADDRESS)
    conr = GameConnector()

    try:
        #TODO: test with meaningful messages
        m = conr.reg_msg("anita")
        sock.sendall(m)
        print(conr.recv(sock))
    finally:
        sock.close()
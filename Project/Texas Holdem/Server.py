import socket
from select import select # for non blocking sockets
import sys

class Server(object):
    """
    Server that adds players to games
     maintains user information
    """
    timeout = 60 # seconds

    def __init__(self):
        self.users = []
        self.tables = []
    def start(self, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a socket object
        server_socket.setblocking(0) # Non blocking
        host = server_socket.gethostname() # Get local machine name
        server_socket.bind((host, port)) # Bind to the port
        self.active_sockets = [server_socket] # Setup sockets to read from 

        server_socket.listen(5) # Now wait for client connection

        while True:
            read_ready, _dummy, _dummy = select(self.active_sockets, [], [], Server.timeout)
            
            for s in read_ready:
                if s is server_socket:
                    client, addr = server_socket.accept() # Establish connection with new client
                    sys.stderr.write('Got connection from: ' + addr)
                    self.active_sockets.append(client)
                    read_ready.remove(server_socket)
                else:
                    pass 
                    # TODO:
                    # recv dict and pickle.loads it 
                    # get request type and username
                    # handle request
    def send_table(self, client):
        # TODO: 
        # get_open_table(username)
        # put in dict -> pickle dumps
        # send table info
        client.close() # Close the connection
    def create_new_table(self):
        pass
    def create_new_user(self, username):
        new_user = {"username" : username,
                    "num_chips" : 150,
                    "last_table" : -1}

        self.users.append(new_user)
    def get_open_table(self, username):
        # TODO: 
        # if new username
        #   create_new_user
        # if no open tables
        #   user is first player
        #   user will be the "server"
        #   send user a port they should start the "server" on and keep track of it
        # else
        #   return ip and port of peer who is the "server"

        # TODO: look into struct library to pack and send data
        pass
    def cash_out(self, client):
        # TODO: do something else related to cash
        client.close() # Close the connection



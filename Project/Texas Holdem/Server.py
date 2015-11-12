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
                    # if client has data_len to be recieved
                    #   while data_recieved < data_len
                    #       recv dict
                    #   pickle.loads it 
                    #   get request type and username
                    #   handle request
                    #   reset data_len of client
                    # else
                    #   recv until deliminator to get data_len client wants to send
                    #   store it
                    #   send ok to client
    def send_table(self, client):
        # TODO: 
        # get_open_table(username)
        # put in dict -> pickle dumps
        # send table info
        # (get verification)
        client.close() # Close the connection
    def create_new_table(self, ip_address, port):
        pass
    def create_new_user(self, username):
        new_user = {"username" : username,
                    "num_chips" : 150,
                    "last_table" : -1,
                    "data_to_receive" : 0}

        self.users.append(new_user)
    def get_open_table(self, username):
        # TODO: 
        # if new username
        #   create_new_user
        # if no open tables
        #   user is first player
        #   user will be the "server"
        #   send user a port they should start the "server" on and keep track of it
        #   (maybe have verification from client that server is started)
        # else
        #   return ip and port of peer who is the "server"
        #   update record (maybe have verification that user joined the table)

        # TODO: look into struct library to pack and send data
        pass
    def cash_out(self, client):
        # TODO: print the value they earned and remove their user information
        client.close() # Close the connection
    def buy_chips(self, amount):
        pass



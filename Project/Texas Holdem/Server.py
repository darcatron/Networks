import socket
from select import select # for non blocking sockets
import sys # logging
import pickle # send and recv python dict data

class Server(object):
    """
    Server that adds players to games
     maintains user information
    """
    timeout = 60 # seconds

    def __init__(self):
        self.users = [] # all poker players (offline or online)
        self.tables = [] # active poker tables
        self.active_sockets = [] # sockets to read from
        self.socket_infos = [] # info about each connected client
    def start(self, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a socket object
        server_socket.setblocking(0) # Non blocking
        host = socket.gethostname() # Get local machine name
        server_socket.bind((host, port)) # Bind to the port
        server_socket.listen(5) # Now wait for client connection

        self.active_sockets.append(server_socket) # Setup sockets to read from 

        while True:
            sys.stderr.write("active_sockets: " + str(self.active_sockets) + "\n\n")
            read_ready, write_ready, errs = select(self.active_sockets, [], [], Server.timeout)
            
            for s in read_ready:
                if s is server_socket:
                    client, addr = server_socket.accept() # Establish connection with new client
                    sys.stderr.write('Got connection from: ' + str(addr) + str(client) + "\n\n")
                    self.active_sockets.append(client)
                    self.socket_infos.append({"socket_number" : client,
                                                "data_to_receive" : 0})
                    read_ready.remove(server_socket)
                else:
                    sys.stderr.write("trying to recieve data from " + str(s) + "\n\n")
                    data_to_receive = self.data_to_recv(s)

                    if data_to_receive:
                        chunks = []
                        bytes_recvd = 0

                        while bytes_recvd < data_to_receive:
                            chunk = s.recv(min(data_to_receive - bytes_recvd, 2048))
                            sys.stderr.write("recvd data: " + str(pickle.loads(chunk)) + "\n")
                            if chunk == '':
                                # TODO: handle err
                                raise RuntimeError("socket connection broken")
                            chunks.append(chunk)
                            bytes_recvd += len(chunk)
                        self.handle_req(s, pickle.loads(''.join(chunks)))
                        #   remove s from active_sockets
                        socket_index = self.get_index_of_socket(s)
                        if socket_index >= 0:
                            self.active_sockets.pop(socket_index)
                        else:
                            raise RuntimeError("s does not exist")
                    else:
                        # get data size to send from client
                        client_data = pickle.loads(s.recv(1024))
                        sys.stderr.write("recvd req: " + str(client_data) + "\n\n")
                        # TODO: handle bad req from client (no data_size_to_send key)
                        self.set_data_to_recv(s, client_data["data_size_to_send"])
                        # send data size to receive to client (ACK)
                        sent = s.send(pickle.dumps({"data_size_to_receive" : client_data["data_size_to_send"]}))
                        if sent == 0:
                            raise RuntimeError("socket connection broken")
    def data_to_recv(self, socket_num):
        socket_index = self.get_index_of_socket(socket_num)
        if socket_index >= 0:
            # return value is >= 0 (bytes)
            return self.socket_infos[socket_index]["data_to_receive"]

        raise RuntimeError("socket_num does not exist!")
    def set_data_to_recv(self, socket_num, recv_size):
        socket_index = self.get_index_of_socket(socket_num)
        if socket_index >= 0:
            self.socket_infos[socket_index]["data_to_receive"] = recv_size
            return

        raise RuntimeError("socket_num does not exist!")
    def get_index_of_socket(self, socket_num):
        for index, connected_socket in enumerate(self.socket_infos):
            if connected_socket["socket_number"] is socket_num:
                return index
        # no such socket
        return -1
    def handle_req(self, client_socket, client_req):
        if client_req["type"] == "play":
            sys.stderr.write('Got play request from ' + client_req["username"] + "\n\n")
            # TODO
            # table_data = self.get_open_table(client_req["username"])
            # self.send_data(client_socket, table_data)
        elif client_req["type"] == "cash":
            # TODO
            sys.stderr.write('Got cash out request from ' + client_req["username"])
        elif client_req["type"] == "buy":
            # TODO
            sys.stderr.write('Got buy chips request from ' + client_req["username"])
        else:
            # TODO: handle bad req
            sys.stderr.write("bad req!" + "\n\n")
    @staticmethod
    def send_data(client_socket, data_to_send):
        # TODO
        totalsent = 0

        while totalsent < len(data_to_send):
            sent = client_socket.send(data_to_send[totalsent:])
            sys.stderr.write("sent " + str(sent) + " bytes to socket " + str(client_socket))
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent += sent

        sys.stderr.write("closing socket " + str(client_socket))
        client_socket.close()
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
                    "last_table" : -1}

        self.users.append(new_user)
    def cash_out(self, client):
        # TODO: print the value they earned and remove their user information
        client.close() # Close the connection
    def buy_chips(self, amount):
        pass



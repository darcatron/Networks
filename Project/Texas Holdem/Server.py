import socket
from select import select # for non blocking sockets
import sys # logging
import pickle # send and recv python dict data
from random import randint

class Server(object):
    """
    Server that adds players to games
     maintains user information
    """
    MAXPLAYERSPERTABLE = 5
    timeout = 30 # seconds

    def __init__(self):
        self.users = [] # all poker players (offline or online)
        self.tables = [] # active poker tables
        self.active_sockets = [] # sockets to read from
        self.socket_infos = [] # info about each connected client
    def start(self, port):
        # TODO: add mimic_down on d keystroke
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a socket object
        server_socket.setblocking(0) # Non blocking
        host = socket.gethostname() # Get local machine name
        server_socket.bind((host, port)) # Bind to the port
        server_socket.listen(5) # Now wait for client connection

        self.active_sockets.append(server_socket) # Setup sockets to read from 

        while True:
            sys.stderr.write("active_sockets: " + str(self.active_sockets) + "\n\n")
            sys.stderr.write("socket_infos: " + str(self.socket_infos) + "\n\n")
            read_ready, _dummy, _dummy = select(self.active_sockets, [], [], Server.timeout)

            for s in read_ready:
                if s is server_socket:
                    client, addr = server_socket.accept() # Establish connection with new client
                    sys.stderr.write('Got connection from: ' + str(addr) + " " + str(client) + "\n\n")
                    self.active_sockets.append(client)
                    self.socket_infos.append({"socket_number" : client,
                                                "host" : addr[0],
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
                        self.active_sockets.pop(self.active_sockets.index(s))
                        socket_index = self.get_index_of_socket_info(s)
                        if socket_index >= 0:
                            self.socket_infos.pop(socket_index)
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
        socket_index = self.get_index_of_socket_info(socket_num)
        if socket_index >= 0:
            # return value is >= 0 (bytes)
            return self.socket_infos[socket_index]["data_to_receive"]

        raise RuntimeError("socket_num does not exist!")
    def set_data_to_recv(self, socket_num, recv_size):
        socket_index = self.get_index_of_socket_info(socket_num)
        if socket_index >= 0:
            self.socket_infos[socket_index]["data_to_receive"] = recv_size
            return

        raise RuntimeError("socket_num does not exist!")
    def get_index_of_socket_info(self, socket_num):
        for index, connected_socket in enumerate(self.socket_infos):
            if connected_socket["socket_number"] is socket_num:
                return index
        # no such socket
        return -1
    def handle_req(self, client_socket, client_req):
        if client_req["type"] == "play":
            sys.stderr.write('Got play request from ' + client_req["username"] + "\n\n")
            table_data = self.get_open_table(self.get_host(client_socket), client_req["username"])
            sys.stderr.write("table_data returned: " + str(table_data) + "\n")
            if "new_table" not in table_data:
                sys.stderr.write("added false to table_data" + "\n")
                table_data["new_table"] = False
            table_data["num_chips"] = self.get_num_chips(client_req["username"])
            sys.stderr.write("updated table_data: " + str(table_data) + "\n\n")
            del table_data["num_players"] # remove extra data
                
            self.send_data(client_socket, table_data)
        elif client_req["type"] == "cash":
            sys.stderr.write('Got cash out request from ' + client_req["username"] + "\n\n")
            self.cash_out(client_req["username"], client_req["amount"])
        elif client_req["type"] == "buy":
            sys.stderr.write('Got buy chips request from ' + client_req["username"] + "\n\n")
            self.buy_chips(client_req["username"], client_req["amount"])
        elif client_req["type"] == "game_update":
            sys.stderr.write("Got update req from " + str(client_req["host"]) + "\n\n")
            self.update_info(client_req)
            sys.stderr.write("new users: " + str(self.users) + "\n\n")
            sys.stderr.write("new tables: " + str(self.tables) + "\n\n")
        elif client_req["type"] == "game_down":
            sys.stderr.write("Got game down req on table with host " + str(client_req["host"]) + "\n\n")
            self.remove_table(client_req["host"])
            sys.stderr.write("tables are now: " + str(self.tables) + "\n\n")
        else:
            # TODO: handle bad req
            sys.stderr.write("bad req!" + "\n\n")

        sys.stderr.write("closing socket " + str(client_socket) + "\n\n")
        client_socket.close() # Close the connection
    def get_host(self, client_socket):
        socket_index = self.get_index_of_socket_info(client_socket)
        return self.socket_infos[socket_index]["host"]            
    @staticmethod
    def send_data(client_socket, data_to_send):
        sys.stderr.write("trying to send" + str(data_to_send) + "\n\n")
        # set up transmission size data
        data_to_send = pickle.dumps(data_to_send)
        data_size_info = {"data_size_to_send" : len(data_to_send)}
        # send notification that sending will start
        client_socket.send(pickle.dumps(data_size_info))
        sys.stderr.write("sent notification" + "\n")
        # wait until socket is ready
        read_ready, _dummy, _dummy = select([client_socket], [], [], Server.timeout)
        # recieve ack
        if read_ready:
            ack = client_socket.recv(1024)
            sys.stderr.write("ack recieved: " + str(pickle.loads(ack)) + "\n")
        else:
            raise RuntimeError("never received ack")

        # send data
        totalsent = 0

        while totalsent < data_size_info["data_size_to_send"]:
            sent = client_socket.send(data_to_send[totalsent:])
            sys.stderr.write("sent " + str(sent) + " bytes to socket " + str(client_socket) + "\n\n")
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent += sent
    def get_open_table(self, host, username):
        sys.stderr.write("trying to find table" + "\n\n")
        if username not in [p["username"] for p in self.users]:
            self.add_new_user(username)
            sys.stderr.write("created new user" + "\n\n")
        
        for table in self.tables:
            if table["num_players"] < Server.MAXPLAYERSPERTABLE:
                table["num_players"] += 1
                sys.stderr.write("found open table: " + str(table) + "\n\n")
                return dict(table)
        # no open tables, player will be "server"
        new_table = self.add_new_table(host, randint(8000, 9000))
        new_table["new_table"] = True
        # user will be assigned a port to start the "server" on
        return new_table
    def get_num_chips(self, username):
        for user in self.users:
            if user["username"] == username:
                return user["num_chips"]
    def add_new_table(self, host, port):
        new_table = {"num_players" : 1,
                     "host" : host,
                     "port" : port}
        self.tables.append(new_table)
        return dict(new_table)
    def remove_table(self, host):
        for index, table in enumerate(self.tables):
            if table["host"] == host:
                return self.tables.pop(index) 
    def add_new_user(self, username):
        new_user = {"username" : username,
                    "num_chips" : 150}

        self.users.append(new_user)
        return new_user
    def cash_out(self, username, amount):
        self.update_chips(username, self.get_num_chips(username) - amount)
    def buy_chips(self, username, amount):
        self.update_chips(username, amount)
    def update_chips(self, username, new_num_chips):
        for user in self.users:
            if user["username"] == username:
                user["num_chips"] = new_num_chips
                return
    def update_info(self, updated_info):
        # update table entry
        for table in self.tables:
            if table["host"] == updated_info["host"]:
                table["num_players"] = updated_info["num_players"]
                break
        # update each player
        for player in updated_info["player_data"]:
            self.update_chips(player["username"], player["num_chips"])


import socket
from select import select # for non blocking sockets
import sys # logging
import pickle # send and recv python dict data
import Dealer

import deuces
from deuces import Card
#from deuces import Deck
#from deuces import Evaluator

#from Dealer import Dealer

class Player(object):
    """
    Information and possible actions of user 
     that is sitting in a poker table
    """
    timeout = 5
    MAXPLAYERS = 5

    def __init__(self, username):
        self.username = username
        
        # connection info
        self.is_dealer = False
        self.dealer = None
        self.players_list = []
        self.peers = [] # socket info of other players (used by main_peer)
        self.main_peer = None # socket connection
        self.table_host = None # player who is hosting the table
        self.backup_peer = None # TODO
        self.recv_socket = None #For dealer, this is socket to send to this player
        self.server_host = None # Poker server
        self.server_port = None
        self.disconnected = False

        # game info
        self.dealer_token = 0
        self.hand = None
        # TODO: fix this so that it's based off what the player says in data
        self.chips = 0
        self.made_move_this_turn = False
        self.has_folded = False
        self.chips_in_pot = 0
        self.chips_in_pot_this_turn = 0
    def add_player(self, player):
        self.players_list.append(player)
    def bet(self, amount): # TODO: NEED TO ADD ERROR CONDITIONS AND ALL IN SPLIT POT
        if amount < self.chips:
            self.chips -= amount
            self.chips_in_pot += amount
            self.chips_in_pot_this_turn += amount
        elif self.chips <= 0: # TODO: return None?
            return None # Stops player from betting more, or remove player from the game
        else:# ALL IN CONDITION
            self.chips_in_pot += self.chips
            self.chips = 0
    def add(self, amount):
        self.chips += amount
    def new_hand(self):
        self.has_folded = False
        self.chips_in_pot = 0
        self.chips_in_pot_this_turn = 0
    def find_game(self, server_port, host=None):
        # connect to poker server
        if host == None:
            host = socket.gethostname()
        self.server_host, self.server_port = host, server_port
        client_socket = socket.socket()
        client_socket.connect((host, server_port))
        # create req for game
        req_data = {"type" : "play", "username" : self.username}
        data_to_send = {"data_size_to_send" : len(pickle.dumps(req_data))}
        # send notification that sending will start
        client_socket.send(pickle.dumps(data_to_send))
        # recieve ack
        ack = client_socket.recv(1024)
        sys.stderr.write("ack recieved: " + str(pickle.loads(ack)) + "\n")
        # send req for game
        client_socket.send(pickle.dumps(req_data))
        sys.stderr.write("sent req for game" + "\n")
        # recv notification that sending will start
        recv_info = pickle.loads(client_socket.recv(1024))
        sys.stderr.write("recvd notification for game info sending" + "\n")
        # send ack
        ack_data = {"data_size_to_receive" : recv_info["data_size_to_send"]}
        client_socket.send(pickle.dumps(ack_data))
        sys.stderr.write("sent ack" + "\n")
        # recv game data
        game_data = self.get_data(client_socket, recv_info["data_size_to_send"])
        self.chips = game_data["num_chips"] # reload chips
        self.table_host = game_data["host"] # set table host
        sys.stderr.write("got game data" + "\n")
        
        if game_data["new_table"]:
            # player is "server", start "sever" for peers
            sys.stderr.write("starting peer server" + "\n")
            self.start_server(game_data["port"])
        else:
            # connect to peer
            try:
                self.main_peer = socket.socket()
                self.main_peer.connect((self.table_host, game_data["port"]))
                self.main_peer.send(pickle.dumps({"username" : self.username, "num_chips" : self.chips}))
                self.play_game()
            except:
                sys.stderr.write("could not connect to table!" + "\n\n")
                self.update_server()
                self.find_game(server_port, host)
    def play_game(self):
        print "Waiting to join game"

        while(True):
            # TODO: find a way to check if player has d/c from game within Dealer
            #       if d/c send a lower value for update_server(num_players)
            #       then remove player from players_list
            #self.update_server(len(self.players_list))
            if self.is_dealer and len(self.players_list) < Player.MAXPLAYERS:
                # check for new player
                if self not in self.players_list: #NEW LINES
                    self.add_player(self)
                read_ready, _dummy, _dummy = select([self.main_peer], [], [], Player.timeout)
                if read_ready:
                    client, addr = self.main_peer.accept() # Establish connection with new client
                    sys.stderr.write('Got connection from: ' + str(addr) + str(client) + "\n\n")
                    # get username and starting chip value from new player
                    client_data = pickle.loads(client.recv(1024))
                    sys.stderr.write("recvd req: " + str(client_data) + "\n\n")
                    
                    p = Player(client_data["username"])
                    p.recv_socket = client
                    p.chips = client_data["num_chips"]
                    self.add_player(p)
                
            #Playing round
            if (not self.is_dealer) or (self.is_dealer and len(self.players_list) > 1):

                #sys.stderr.write("Length is long enough" + "\n\n")
                if self.is_dealer: #DEALER CODE
                    d = Dealer.Dealer()
                    d.AddPlayers(self.players_list)
                    self.dealer_token = (self.dealer_token + 1)%len(self.players_list)
                    d.DealHand(self.dealer_token)
                else:
                    id_num = 0
                    while(id_num != 5): #PLAYER CODE
                        msg = self.main_peer.recv(1024)
                        if msg == "":
                            self.update_server()
                            print "The host has gone offline. Please reconnect at a new table."
                            return
                        else:
                            msg = pickle.loads(msg)
                        id_num = msg["id"]
                        if id_num == 1: #Print
                            print msg["print"]
                        elif id_num == 2: #F,C,B
                            if msg["board"]:
                                Card.print_pretty_cards(msg["board"])
                            Card.print_pretty_cards(msg["hand"])
                            print 'Pot size is: %d. You have %d remaining chips' % (msg["pot"], msg["chips"])
                            move = raw_input('Fold (F), Check (CH), or Bet (B-numChips)? ')
                            self.main_peer.send(pickle.dumps({"id" : 4, "move" : move}))
                        elif id_num == 3: #F,C,R
                            if msg["board"]:
                                Card.print_pretty_cards(msg["board"])
                            Card.print_pretty_cards(msg["hand"])
                            print 'Pot size is: %d. Call %d to stay in. You have %d remaining chips' % (msg["pot"], msg["curr_bet"], msg["chips"])
                            move = raw_input('Fold (F), Call (C), or Raise (R-numChips)? ')
                            self.main_peer.send(pickle.dumps({"id" : 4, "move" : move}))
                        elif id_num == 5:
                            victory_string = msg["print"]
                            print victory_string.replace(self.username, "you")
                            #print msg["print"]
                        elif id_num == 6: #Input error
                            move = raw_input('Wrong input format. Please enter again: ')
                            self.main_peer.send(pickle.dumps({"id" : 4, "move" : move}))
                        else:
                            continue
                        id_num = 0    
                
            #Leave function if have 0 chips left
            if self.chips <= 0:
                print "You have no chips. Please purchase more chips to continue playing."
                return
    def start_server(self, port):
        self.is_dealer = True
        self.dealer = Dealer.Dealer()
        self.main_peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a socket object
        # self.main_peer.setblocking(0) # Non blocking
        self.main_peer.bind((self.table_host, port)) # Bind to the port given by server
        self.main_peer.listen(5) # Now wait for peer connection
        self.play_game()
    def update_server(self, num_players=None):
        # create req for update    
        req_data = {"host" : self.table_host}

        if self.is_dealer:
            # get game data
            player_data = []

            for p in self.players_list:
                player_data.append({"username" : p.username, 
                                    "num_chips" : p.chips})
            req_data["type"] = "game_update"
            req_data["num_players"] = num_players
            req_data["player_data"] = player_data
        else:
            req_data["type"] = "game_down"

        # connect to poker server
        client_socket = socket.socket()
        client_socket.connect((self.server_host, self.server_port))
        # send notification that sending will start
        data_to_send = {"data_size_to_send" : len(pickle.dumps(req_data))}
        client_socket.send(pickle.dumps(data_to_send))
        # recieve ack
        ack = client_socket.recv(1024)
        sys.stderr.write("ack recieved: " + str(pickle.loads(ack)) + "\n")
        # send game data
        req_data = pickle.dumps(req_data)
        totalsent = 0

        while totalsent < data_to_send["data_size_to_send"]:
            sent = client_socket.send(req_data[totalsent:])
            sys.stderr.write("sent " + str(sent) + " bytes to socket " + str(client_socket) + "\n\n")
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent += sent
        sys.stderr.write("sent status update" + "\n")
    @staticmethod
    def get_data(connected_socket, num_bytes_to_receive):
        chunks = []
        bytes_recvd = 0
        sys.stderr.write("in get_data" + "\n\n")
        while bytes_recvd < num_bytes_to_receive:
            chunk = connected_socket.recv(min(num_bytes_to_receive - bytes_recvd, 2048))
            sys.stderr.write("recvd data: " + str(pickle.loads(chunk)) + "\n")
            if chunk == '':
                # TODO: handle err
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recvd += len(chunk)
            sys.stderr.write("recieved bytes: " + str(bytes_recvd) + "\n\n")

        return pickle.loads(''.join(chunks))

#pList = []
#p = Player('Sean')
#p.is_dealer=True
#pList.append(p)
#pList.append(Player('Bob'))
#pList.append(Player('Test'))
#pList.append(Player('Blah'))
#pList[0].add_players(pList)
#pList[0].play_game()

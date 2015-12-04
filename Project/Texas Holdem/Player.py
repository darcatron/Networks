import socket
import sys # logging
import pickle # send and recv python dict data
import Dealer #import deuces

#from deuces import Card
#from deuces import Deck
#from deuces import Evaluator

#from Dealer import Dealer

class Player(object):
    """
    Information and possible actions of user 
     that is sitting in a poker table
    """
    starting_chips = 150

    def __init__(self, username):
        self.username = username

        self.my_socket = None
        self.is_dealer = False
        self.players_list = []
        self.main_peer = None
        self.backup_peer = None # TODO
        
        self.hand = None
        self.chips = Player.starting_chips
        self.made_move_this_turn = False
        self.has_folded = False
        self.chips_in_pot = 0
        self.chips_in_pot_this_turn = 0
    def add_players(self, players):#Temporary Function
        # TODO: maybe just have this function take in a player name and 
        #       add it to the list rather than overwrite the list
        self.players_list = players
    def bet(self, amount): # TODO: NEED TO ADD ERROR CONDITIONS AND ALL IN SPLIT POT
        if amount < self.chips:
            self.chips -= amount
            self.chips_in_pot += amount # TODO: shouldn't be for player
            self.chips_in_pot_this_turn += amount # TODO: chips player put in??
        elif self.chips <= 0: # TODO: return None?
            None # Stops player from betting more, or remove player from the game
        else:# ALL IN CONDITION
            self.chips_in_pot += self.chips
            self.chips = 0
    def add(self, amount):
        self.chips += amount
    def new_hand(self):
        self.has_folded = False
        self.chips_in_pot = 0
        self.chips_in_pot_this_turn = 0
    def find_game(self, server_port):
        # connect to poker server
        client_socket = socket.socket()
        client_socket.connect((socket.gethostname(), server_port))
        # create req for game
        req_data = {"type" : "play", "username" : self.username}
        data_to_send = {"data_size_to_send" : len(pickle.dumps(req_data))}
        # send notification that sending will start
        client_socket.send(pickle.dumps(data_to_send))
        # recieve ack
        ack = client_socket.recv(1024)
        sys.stderr.write("ack recieved: " + str(pickle.loads(ack)) + "\n\n")
        # send req for game
        client_socket.send(pickle.dumps(req_data))
        # recv notification that sending will start
        recv_info = self.get_data(client_socket, 1024)
        # send ack
        client_socket.send({"data_size_to_receive" : recv_info["data_size_to_send"]})
        # recv game data
        game_data = self.get_data(client_socket, recv_info["data_size_to_send"])
        
        if game_data["new_table"]:
            # player is "server", start "sever" for peers
            self.start_server()
            # TODO: setup gamestate info
        else:
            # connect to peer
            self.main_peer = socket.socket()
            self.main_peer.connect((game_data["host"], game_data["port"]))
    def play_game(self):
        if self.is_dealer: #Sends dealers to another function
            self.deal_game()
        
        id_num = 0
        while(id_num != 5):
            msg = pickle.loads(self.my_socket.recv(1024))
            id_num = msg["id"]
            if id_num == 1: #Print
                print msg["print"]
            elif id_num == 2: #F,C,B
                if msg["board"]:
                    Card.print_pretty_cards(msg["board"])
                Card.print_pretty_cards(msg["hand"])
                print 'Pot size is: %d. You have %d remaining chips' % (msg["pot"], msg["chips"])
                move = raw_input('Fold (F), Check (C), or Bet (B-numChips)? ')
                self.main_peer.send(pickle.dumps({"id" : 4, "move" : move}))
            elif id_num == 3: #F,C,R
                if msg["board"]:
                    Card.print_pretty_cards(msg["board"])
                Card.print_pretty_cards(msg["hand"])
                print 'Pot size is: %d. Call %d to stay in. You have %d remaining chips' % (msg["pot"], msg["curr_bet"], msg["chips"])
                move = raw_input('Fold (F), Call (C), or Raise (R-numChips)? ')
                self.main_peer.send(pickle.dumps({"id" : 4, "move" : move}))
            elif id_num == 5:
                print msg["print"]
                                                                                            

    def deal_game(self):
        d = Dealer.Dealer()
        d.AddPlayers(self.players_list)
        dealer_token = 0
        
        while len(self.players_list) > 1:#Really should be as long as there are more than 1 players with money
            dealer_token = (dealer_token + 1)%len(self.players_list)
            d.DealHand(dealer_token)


    def start_server(self):
        self.is_dealer = True
        # TODO: peer is Dealer
        # start TexasHoldem game
        # if new hand, wait a few seconds for new player requests
        # get moves from each peer
        pass
    def get_gamestate(self):
        # TODO: parse gamestate data and update self
        # TODO: look into pickle library to unserialize data
        pass
    def get_data(self, connected_socket, data_to_receive):
        chunks = []
        bytes_recvd = 0

        while bytes_recvd < data_to_receive:
            chunk = connected_socket.recv(min(data_to_receive - bytes_recvd, 2048))
            sys.stderr.write("recvd data: " + str(pickle.loads(chunk)) + "\n")
            if chunk == '':
                # TODO: handle err
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recvd += len(chunk)

        return pickle.loads(''.join(chunks))
    def send_gamestate(self):
        # TODO: if player is server
        # send gamestate to each player
        # TODO: look into pickle library to serialize and send data
        pass

pList = []
p = Player('Sean')
p.is_dealer=True
pList.append(p)
pList.append(Player('Bob'))
pList.append(Player('Test'))
pList.append(Player('Blah'))
pList[0].add_players(pList)
pList[0].play_game()




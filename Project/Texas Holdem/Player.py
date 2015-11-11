class Player(object):
    """
    Information and possible actions of user 
     that is sitting in a poker table
    """
    starting_chips = 150

    def __init__(self, username):
        self.username = username
        self.hand = None
        self.chips = Player.starting_chips
        self.made_move_this_turn = False
        self.has_folded = False
    def bet(self, amount): # TODO: NEED TO ADD ERROR CONDITIONS AND ALL IN SPLIT POT
        if amount < self.chips:
            self.chips -= amount
            self.chipsInPot += amount # TODO: shouldn't be for player
            self.chipsInPotThisTurn += amount # TODO: chips player put in??
        elif self.chips <= 0: # TODO: return None?
            None # Stops player from betting more, or remove player from the game
        else:# ALL IN CONDITION
            self.chipsInPot += self.chips
            self.chips = 0
    def add(self, amount):
        self.chips += amount
    def new_hand(self):
        self.has_folded = False
        self.chipsInPot = 0
        self.chipsInPotThisTurn = 0
    def find_game(self):
        # TODO: 
        # req server for game
        # if player is "server"
        #   setup gamestate info
        #   start "sever" for new peers
        # else 
        #   connect to peer
        pass
    def play_game(self):
        # TODO: peer is connected to another peer that is the "server"
        # get_gamestate from "server"
        # send "server" move
        # TODO: look into pickle library to serialize and send data
        pass
    def start_server(self):
        # TODO: peer is Dealer
        # start TexasHoldem game
        # if new hand, wait a few seconds for new player requests
        # get moves from each peer
        pass
    def get_gamestate(self):
        # TODO: parse gamestate data and update self
        # TODO: look into pickle library to unserialize data
        pass
    def send_gamestate(self):
        # TODO: if player is server
        # send gamestate to each player
        # TODO: look into pickle library to serialize and send data
        pass

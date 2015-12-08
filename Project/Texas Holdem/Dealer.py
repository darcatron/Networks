import deuces
import pickle

from deuces import Card
from deuces import Deck
from deuces import Evaluator


class Dealer(object):
    """
    Dealer for Texas Hold'em game
    """
    large_blind_amount = 2
    small_blind_amount = 1
    MAXPLAYERS = 5

    def __init__(self):
        import Player #Placed here to avoid circular dependency on imports
        self.players = []
        self.total_pot = 0
        self.board = None
        self.dealer_token = 0
        self.num_disconnect = 0
    
    def AddPlayers(self, playerL):#Not right
        self.players = playerL

    def Blinds(self):
        smallBlind = (self.dealer_token + 1)%len(self.players)
        largeBlind = (self.dealer_token + 2)%len(self.players)
        self.players[smallBlind].bet(self.small_blind_amount)
        self.players[largeBlind].bet(self.large_blind_amount)
    
    def TotalPot(self):
        total = 0
        for p in self.players:
            total += p.chips_in_pot
        return total

    def update(self):
        for p in self.players:
            if p.is_dealer:
                p.update_server(len(self.players)-self.num_disconnect)
            
    def removePlayer(self, turn):
        self.players[turn].disconnected = True
        self.num_disconnect += 1
        self.update()
        return pickle.loads(pickle.dumps({"id" : 4, "move" : "F"}))
    
    def SendMessageToAll(self, turn, msg):
        unpickled = pickle.loads(msg)
        for p in self.players:
            if (self.players.index(p) != turn) and not p.has_folded:
                if not(p.is_dealer):
                    try:
                        p.recv_socket.send(msg)
                    except:
                        self.removePlayer(self.players.index(p))
                else:
                    print unpickled["print"]
    
    def LastFolded(self):
        total = 0
        for p in self.players:
            if p.has_folded:
                None
            else:
                total += 1
                
        if total == 1:
            return True
        else:
            return False

    def FoldVictory(self):
        for p in self.players:
            if not(p.has_folded):
                p.add(self.TotalPot())
                self.SendMessageToAll(-1, pickle.dumps({"id" : 5, "print" : p.username + " wins on fold"}))

    def dividePot(self, winners):
        numWinners = len(winners)
        for w in winners:
           self.players[w].add(self.TotalPot() // numWinners) #//->To force whole numbers

    def RankedVictory(self):
        evaluator = Evaluator()
        best_rank = 7463 # One less than worse rank
        winners = []
        for p in self.players:
            rank = evaluator.evaluate(self.board, p.hand)
    
            if rank == best_rank:
                winners.append(self.players.index(p))#Adding index of winner to list
                best_rank = rank
                #To get the class of the victory to print
                rank_class = evaluator.get_rank_class(rank)
                class_string = evaluator.class_to_string(rank_class)
            elif rank < best_rank:
                winners = [self.players.index(p)]
                best_rank = rank
                rank_class = evaluator.get_rank_class(rank)
                class_string = evaluator.class_to_string(rank_class)
            
        self.dividePot(winners)
    
        if len(winners) == 1:
            self.SendMessageToAll(-1, pickle.dumps({"id" : 5, "print" : self.players[winners[0]].username + " wins with " + class_string}))
        else:
            #Edge Case. Not accounted for in messages
            self.SendMessageToAll(-1, pickle.dumps({"id" : 5, "print" : self.players[winners[0]].username + " wins with " + class_string}))

    def MoveOutput(self, turn, move):
        if move == 'F':
            self.SendMessageToAll(turn, pickle. dumps({"id" : 1, "print" : self.players[turn].username + " folded"}))
        elif move == 'C':
            self.SendMessageToAll(turn, pickle.dumps({"id" : 1, "print" : self.players[turn].username + " called"}))
        elif move == 'CH':
            self.SendMessageToAll(turn, pickle.dumps({"id" : 1, "print" : self.players[turn].username + " checked"}))
        elif move[0] == 'R':
            self.SendMessageToAll(turn, pickle.dumps({"id" : 1, "print" : self.players[turn].username + " raised by " + move[2:]}))
        elif move[0] == 'B':
            self.SendMessageToAll(turn, pickle.dumps({"id" : 1, "print" : self.players[turn].username + " bet " + move[2:]}))

#     NOTE: The following code is extremely messy
#        The purpose of this function is basically to mitigate a single round
#        of betting. It sends move queries to players, and then receives and acts
#        on their responses.

    def Bets(self,startingPlayer, startingAmount):
        turn = startingPlayer
        toPay = startingAmount
        response = {}
    
        for p in self.players:
            p.made_move_this_turn = False
    
        roundOver = False
        while(not(roundOver)):
            move = '1' #Initialize value in case of fold
            if(self.players[turn].has_folded):
                None
            elif not((self.players[turn].made_move_this_turn)):
                self.SendMessageToAll(turn, pickle.dumps({"id" : 1, "print" : "Waiting on " + self.players[turn].username + "'s turn."}))
                if self.players[turn].is_dealer:
                    if self.board:
                        Card.print_pretty_cards(self.board)
                    Card.print_pretty_cards(self.players[turn].hand)
                
                if self.players[turn].chips_in_pot_this_turn < toPay:
                    if self.players[turn].is_dealer:
                        print 'Pot size is: %d. Call %d to stay in. You have %d remaining chips' % (self.TotalPot(), toPay - self.players[turn].chips_in_pot_this_turn, self.players[turn].chips) 
                        move = raw_input('Fold (F), Call (C), or Raise (R-numChips)? ')
                        response = pickle.loads(pickle.dumps({"id" : 4, "move" : move}))#For consistency
                    else:
                        try:
                            self.players[turn].recv_socket.send(pickle.dumps({"id" : 3, "board" : self.board, "hand" : self.players[turn].hand, "chips" : self.players[turn].chips, "chips_in_pot" : self.players[turn].chips_in_pot, "curr_bet" : toPay - self.players[turn].chips_in_pot_this_turn, "pot" : self.TotalPot()}))
                            receiver_response = self.players[turn].recv_socket.recv(1024)
                        except:
                            receiver_response = ""

                        if receiver_response == "":
                            response = self.removePlayer(turn)
                        else:
                            response = pickle.loads(receiver_response)
                else:
                    if self.players[turn].is_dealer:
                        print 'Pot size is: %d. You have %d remaining chips' % (self.TotalPot(), self.players[turn].chips)
                        move = raw_input('Fold (F), Check (CH), or Bet (B-numChips)? ')
                        response = pickle.loads(pickle.dumps({"id" : 4, "move" : move}))#For consistency
                    else:
                        try:
                            self.players[turn].recv_socket.send(pickle.dumps({"id" : 2, "board" : self.board, "hand" : self.players[turn].hand, "chips" : self.players[turn].chips, "chips_in_pot" : self.players[turn].chips_in_pot, "pot" : self.TotalPot()}))
                            receiver_response = self.players[turn].recv_socket.recv(1024)
                        except:
                            receiver_response = ""
                        if receiver_response == "":
                            response = self.removePlayer(turn)
                        else:
                            response = pickle.loads(receiver_response)
                        
                self.players[turn].made_move_this_turn = True
            else:
                self.SendMessageToAll(turn, pickle.dumps({"id" : 1, "print" : "Waiting on " + self.players[turn].username + "'s turn."}))
                if self.players[turn].chips_in_pot_this_turn < toPay:
                    if self.players[turn].is_dealer:
                        if self.board:
                            Card.print_pretty_cards(self.board)
                        Card.print_pretty_cards(self.players[turn].hand)
                        
                    if self.players[turn].is_dealer:
                        print 'Pot size is: %d. Call %d to stay in. You have %d remaining chips' % (self.TotalPot(), toPay - self.players[turn].chips_in_pot_this_turn, self.players[turn].chips)
                        move = raw_input('Fold (F), Call (C), or Raise (R-numChips)? ')
                        response = pickle.loads(pickle.dumps({"id" : 4, "move" : move}))#For consistency
                    else:
                        try:
                            self.players[turn].recv_socket.send(pickle.dumps({"id" : 3, "board" : self.board, "hand" : self.players[turn].hand, "chips" : self.players[turn].chips, "chips_in_pot" : self.players[turn].chips_in_pot, "curr_bet" : toPay - self.players[turn].chips_in_pot_this_turn, "pot" : self.TotalPot()}))
                            receiver_response = self.players[turn].recv_socket.recv(1024)
                        except:
                            receiver_response = ""
                        if receiver_response == "":
                            response = self.removePlayer(turn)
                        else:
                            response = pickle.loads(receiver_response)
                else:
                    roundOver = True  #If player has already moved, but has nothing to bet
                                           #Then the round is neccesarily over

            
            if "move" not in response.keys():
                response["move"] = 'NA'
            #Handling user input
            response_invalid = True
            while response_invalid:
                if response["move"] == 'F':
                    self.players[turn].has_folded = True
                    roundOver = self.LastFolded()
                    response_invalid = False
                elif response["move"] == 'C' or response["move"] == 'CH':
                    self.players[turn].bet(toPay-self.players[turn].chips_in_pot_this_turn)
                    response_invalid = False
                elif (len(response["move"]) >= 3) and response["move"][0] == 'R':
                    increase = int(response["move"][2:])
                    if increase <= self.players[turn].chips:
                        toPay += increase - (toPay - self.players[turn].chips_in_pot_this_turn)
                        self.players[turn].bet(increase)
                        response_invalid = False
                elif (len(response["move"]) >= 3) and response["move"][0] == 'B':
                    increase = int(response["move"][2:])
                    if increase <= self.players[turn].chips:
                        toPay += increase
                        self.players[turn].bet(increase)
                        response_invalid = False
                elif response["move"] == 'NA': #bug fix
                    break
                if response_invalid:
                    if self.players[turn].is_dealer:
                        move = raw_input('Wrong input format. Please enter again: ')
                        response = pickle.loads(pickle.dumps({"id" : 4, "move" : move}))
                    else:
                        self.players[turn].recv_socket.send(pickle.dumps({"id" : 6}))
                        response = pickle.loads(self.players[turn].recv_socket.recv(1024))
                        if response == "":
                            response = self.removePlayer(turn)
                                                    
            self.MoveOutput(turn, response["move"])
            response["move"]='NA'
            
            turn = (turn+1)%len(self.players)
            
        for p in self.players:
            p.chips_in_pot_this_turn = 0
        
        if self.LastFolded():
            return True
        else:
            return False

    def ResetHands(self):
        for p in self.players:
            p.new_hand()

    def remove_dropped(self):
        for p in list(self.players):
            if p.disconnected:
                self.players.pop(self.players.index(p))

    def DealHand(self, dealer_token):
        self.dealer_token = dealer_token
    
        handOver = False
        deck = Deck()

        self.Blinds()
 
        for p in self.players:
            p.hand = deck.draw(2)

        self.board = []
        numPlayers = len(self.players)
        handOver = self.Bets(((self.dealer_token+3)%numPlayers), self.large_blind_amount)

        if not(handOver):
            self.board = deck.draw(3)
            handOver = self.Bets(((self.dealer_token+1)%numPlayers), 0)

        if not(handOver):
            self.board.append(deck.draw(1))
            handOver = self.Bets(((self.dealer_token+1)%numPlayers), 0)

        if not(handOver):
            self.board.append(deck.draw(1))
            handOver = self.Bets(((self.dealer_token+1)%numPlayers), 0)

        if handOver:
            self.FoldVictory()
        else:
            self.RankedVictory()

        self.update()
        self.remove_dropped()
        self.ResetHands()
        return

    def isGameOver(self):
        total = 0
        for p in self.players:
            if p.chips > 0:
                total += 1

        if total == 1:
            return True
        else:
            return False

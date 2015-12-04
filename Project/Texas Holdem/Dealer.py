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
        import Player #Place here to avoid circular dependency on imports
        self.players = []
        self.total_pot = 0
        self.board = None
        self.dealer_token = 0
    
    def AddPlayers(self, playerL):#Not exactly sure about this. Should player be constructed or passed directly to the function
        self.players = playerL

    #To account for the blinds
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
    def SendMessageToAll(self, msg):
        unpickled = pickle.loads(msg)
        for p in self.players:
            if not(p.is_dealer):
                p.my_socket.send(msg)
            else:
                print unpickled["print"]
    
    #Returns True if all players but one have folded
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

    #Victory for last players who has not folded
    def FoldVictory(self):#MSG SEND MESSAGE TO ALL PEOPLE ABOUT WHO WON DUE TO FOLD VICTORY
        for p in self.players:
            if not(p.has_folded):
                p.add(self.TotalPot())
                self.SendMessageToAll(pickle.dumps({"id" : 5, "print" : p.username + " wins on fold"}))

    def dividePot(self, winners):
        numWinners = len(winners)
        for w in winners:
           self.players[w].add(self.TotalPot() // numWinners) #//->To force whole numbers

    #Victory if multiple players have made it to the end of the hand
    def RankedVictory(self):#MSG SEND MESSAGE TO ALL PEOPLE ABOUT WHO WON DUE TO RANKED VICTORY
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
                #To get the class of the victory to print
                rank_class = evaluator.get_rank_class(rank)
                class_string = evaluator.class_to_string(rank_class)
            
        self.dividePot(winners)
    
        if len(winners) == 1:
            self.SendMessageToAll(pickle.dumps({"id" : 5, "print" : winners[0].username + " wins with " + class_string}))
        else:
            print 'Players x and y win with %s' % class_string #Edge Case

    def dealer_index(self):
        for p in self.players:
            if p.is_dealer:
                return players.index(p)
        

    def Bets(self,startingPlayer, startingAmount):
        #UPDATE GAMESTATE TO BACKUP PLAYER
        turn = startingPlayer
        toPay = startingAmount
    
        for p in self.players:
            p.made_move_this_turn = False
    
        roundOver = False
        while(not(roundOver)):
            move = '1' #Initialize value in case of fold
            if(self.players[turn].has_folded):
                None
            elif not((self.players[turn].made_move_this_turn)):
                
                if self.board:
                    Card.print_pretty_cards(self.board)
                Card.print_pretty_cards(self.players[turn].hand)
                
                if self.players[turn].chips_in_pot_this_turn < toPay:
                    if self.players[turn].is_dealer:
                        print 'Pot size is: %d. Call %d to stay in. You have %d remaining chips' % (self.TotalPot(), toPay - self.players[turn].chips_in_pot_this_turn, self.players[turn].chips) 
                        move = raw_input('Fold (F), Call (C), or Raise (R-numChips)? ')
                        response = pickle.loads(pickle.dumps({"id" : 4, "move" : move}))#For consistency
                        #SendMessageToAll(pickle.dumps({"ID" : 1, "To_Print" : self.players[turn].username + " " + move}))
                    else:
                        #MSG
                        self.players[turn].my_socket.send(pickle.dump({"id" : 3, "board" : self.board, "hand" : self.players[turn].hand, "chips" : self.players[turn].chips, "chips_in_pot" : self.players[turn].chips_in_pot, "curr_bet" : toPay - self.players[turn].chips_in_pot_this_turn, "pot" : self.TotalPot()}))
                        response = pickle.loads(self.players[turn].recv(1024))
                else:
                    if self.players[turn].is_dealer:
                        print 'Pot size is: %d. You have %d remaining chips' % (self.TotalPot(), self.players[turn].chips)
                        move = raw_input('Fold (F), Check (C), or Bet (B-numChips)? ')
                        response = pickle.loads(pickle.dumps({"id" : 4, "move" : move}))#For consistency
                    else:
                        #MSG
                        self.players[turn].my_socket.send(pickle.dump({"id" : 2, "board" : self.board, "hand" : self.players[turn].hand, "chips" : self.players[turn].chips, "chips_in_pot" : self.players[turn].chips_in_pot, "pot" : self.TotalPot()}))
                        response = pickle.loads(self.players[turn].recv(1024))
                        
                self.players[turn].made_move_this_turn = True
            else:
                if self.players[turn].chips_in_pot_this_turn < toPay:
                    if self.board:
                        Card.print_pretty_cards(self.board)
                    Card.print_pretty_cards(self.players[turn].hand)
                    if self.players[turn].is_dealer:
                        print 'Pot size is: %d. Call %d to stay in. You have %d remaining chips' % (self.TotalPot(), toPay - self.players[turn].chips_in_pot_this_turn, self.players[turn].chips)
                        move = raw_input('Fold (F), Call (C), or Raise (R-numChips)? ')
                        response = pickle.loads(pickle.dumps({"id" : 4, "move" : move}))#For consistency
                    else:
                        #MSG
                        self.players[turn].my_socket.send(pickle.dump({"id" : 3, "board" : self.board, "hand" : self.players[turn].hand, "chips" : self.players[turn].chips, "chips_in_pot" : self.players[turn].chips_in_pot, "curr_bet" : toPay - self.players[turn].chips_in_pot_this_turn, "pot" : self.TotalPot()}))
                        response = pickle.loads(self.players[turn].recv(1024))
                else:
                    roundOver = True  #If player has already moved, but has nothing to bet
                                           #Then the round is neccesarily over
            if response["move"] == 'F':
                self.players[turn].has_folded = True
                roundOver = self.LastFolded()
            elif response["move"] == 'C':
                self.players[turn].bet(toPay-self.players[turn].chips_in_pot_this_turn)
                
            #BOTH OF THESE CHECKS WILL BE REMOVED, SINCE PLAYERS WILL NOW UPDATE THE MONEY AS THEY MAKE A DECISION
            elif response["move"][0] == 'R':
                increase = int(response["move"][2:])
                toPay += increase - (toPay - self.players[turn].chips_in_pot_this_turn)
                self.players[turn].bet(increase)
            elif response["move"][0] == 'B':
                increase = int(response["move"][2:])
                toPay += increase
                self.players[turn].bet(increase)

            self.SendMessageToAll(pickle.dumps({"id" : 1, "print" : self.players[turn].username + " " + response["move"]}))
            
            turn = (turn+1)%len(self.players)
            
        #To let the dealer know if the round has ended
        for p in self.players:
            p.chips_in_pot_this_turn = 0
            
        if self.LastFolded():
            return True
        else:
            return False

    def ResetHands(self):
        for p in self.players:
            p.new_hand()

#Simulates a single hand
    def DealHand(self, dealer_token):
        self.dealer_token = dealer_token
    
        handOver = False #True when all but one folds
        deck = Deck()

        self.Blinds()
 
        for p in self.players:
            p.hand = deck.draw(2)

        #MSG SEND GAMESTATE TO BACKUP THAT INCLUDES DECK AND ALL PLAYER HANDS

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

        self.ResetHands()


    #Returns true if only one player has chips left
    def isGameOver(self):
        total = 0
        for p in self.players:
            if p.chips > 0:
                total += 1

        if total == 1:
            return True
        else:
            return False
    
    #Simulates an entire game
    def dealGame(self):
        gameOver = False
        while not(gameOver):
            #Add Players
            self.dealer_token = (self.dealer_token+1)%len(self.players)
            self.DealHand()
            gameOver = self.isGameOver()

#dealer = Dealer()
#dealer.AddPlayer(Player.Player('sean'))
#dealer.AddPlayer(Player.Player('bob'))
#dealer.AddPlayer(Player.Player('tim'))
#dealer.dealGame()

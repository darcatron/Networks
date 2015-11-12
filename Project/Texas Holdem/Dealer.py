import deuces
import Player

from deuces import Card
from deuces import Deck
from deuces import Evaluator

class Dealer(object):
    """
    Dealer for Texas Hold'em game
    """
    large_blind_amount = 2
    small_blind_amount = 1

    def __init__(self):
        self.players = []
        self.total_pot = 0
        self.board = None
        self.dealer_token = 0
    
    def AddPlayer(self, player):#Not exactly sure about this. Should player be constructed or passed directly to the function
        self.players.append(player)

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
    def FoldVictory(self):
        for p in self.players:
            if not(p.has_folded):
                p.add(self.TotalPot())

    def dividePot(self, winners):
        numWinners = len(winners)
        for w in winners:
           self.players[w].add(self.TotalPot() // numWinners) #//->To force whole numbers

    #Victory if multiple players have made it to the end of the hand
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
                #To get the class of the victory to print
                rank_class = evaluator.get_rank_class(rank)
                class_string = evaluator.class_to_string(rank_class)
            
        self.dividePot(winners)
    
        if len(winners) == 1:
            #Will print usernames eventually
            print 'Player x wins with %s' % class_string
        else:
            print 'Players x and y win with %s' % class_string
        

    def Bets(self,startingPlayer, startingAmount):
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
                    print 'Pot size is: %d. Call %d to stay in. You have %d remaining chips' % (self.TotalPot(), toPay - self.players[turn].chips_in_pot_this_turn, self.players[turn].chips) 
                    move = raw_input('Fold (F), Call (C), or Raise (R)? ')
                else:
                    print 'Pot size is: %d. You have %d remaining chips' % (self.TotalPot(), self.players[turn].chips)
                    move = raw_input('Fold (F), Check (C), or Bet (B)? ')
                self.players[turn].made_move_this_turn = True
            else:
                if self.players[turn].chips_in_pot_this_turn < toPay:
                    if self.board:
                        Card.print_pretty_cards(self.board)
                    Card.print_pretty_cards(self.players[turn].hand)
                    print 'Pot size is: %d. Call %d to stay in. You have %d remaining chips' % (self.TotalPot(), toPay - self.players[turn].chips_in_pot_this_turn, self.players[turn].chips)
                    move = raw_input('Fold (F), Call (C), or Raise (R)? ')
                else:
                    roundOver = True  #If player has already moved, but has nothing to bet
                                           #Then the round is neccesarily over
            if move == 'F':
                self.players[turn].has_folded = True
                roundOver = self.LastFolded()
            elif move == 'C':
                self.players[turn].bet(toPay-self.players[turn].chips_in_pot_this_turn)
            elif move == 'R':
                print 'The current bet is %d.' % toPay
                increase = input('How much do you want to raise? ')
                toPay += increase - (toPay - self.players[turn].chips_in_pot_this_turn)
                self.players[turn].bet(increase)
            elif move == 'B':
                increase = input('How much do you want to bet? ')
                toPay += increase
                self.players[turn].bet(increase)
                
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
    def DealHand(self):
    
        handOver = False #True when all but one folds
        deck = Deck()

        self.Blinds()
 
        for p in self.players: #As these are drawn, send to players
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

dealer = Dealer()
dealer.AddPlayer(Player.Player('sean'))
dealer.AddPlayer(Player.Player('bob'))
dealer.AddPlayer(Player.Player('tim'))
dealer.dealGame()

import deuces

from deuces import Card
from deuces import Deck
from deuces import Evaluator

numPlayers = 3

LARGE_BLIND_AMOUNT = 2
SMALL_BLIND_AMOUNT = 1

#Player Class
class Player:
    userName = None #To be used eventually
    hand = None
    chips = 150
    chipsInPot = 0
    chipsInPotThisTurn = 0
    madeMoveThisTurn = False
    hasFolded = False
    def bet(self, amount): #NEED TO ADD ERROR CONDITIONS AND ALL IN SPLIT POT
        if amount < self.chips:
            self.chips -= amount
            self.chipsInPot += amount
            self.chipsInPotThisTurn += amount
        elif self.chips <= 0:
            None #Stops player from betting more, or remove player from the game
        else:#ALL IN CONDITION
            self.chipsInPot += self.chips
            self.chips = 0
    def add(self, amount):
        self.chips += amount
    def newHand(self):
        hasFolded = False
        self.chipsInPot = 0
        self.chipsInPotThisTurn = 0

#Setting up array of all players
PlayerList = []
for i in range(numPlayers):
    PlayerList.append(Player())

#To account for the blinds
def Blinds(DEALER_TOKEN):
    smallBlind = (DEALER_TOKEN + 1)%numPlayers
    largeBlind = (DEALER_TOKEN + 2)%numPlayers

    PlayerList[smallBlind].bet(SMALL_BLIND_AMOUNT)
    PlayerList[largeBlind].bet(LARGE_BLIND_AMOUNT)

def TotalPot():
    total = 0
    for p in PlayerList:
        total += p.chipsInPot
    return total

def LastFolded():
    total = 0
    for p in PlayerList:
        if p.hasFolded:
            None
        else:
            total += 1

    if total == 1:
        return True
    else:
        return False


#All but one player has folded
def FoldVictory():
    for p in PlayerList:
        if not(p.hasFolded):
            p.add(TotalPot())

def dividePot(winners):
    numWinners = len(winners)
    for w in winners:
        PlayerList[w].add(TotalPot() // numWinners) #//->To force whole numbers

def RankedVictory(board):
    evaluator = Evaluator()
    best_rank = 7463 # One less than worse rank
    winners = []
    for p in PlayerList:
        rank = evaluator.evaluate(board, p.hand)

        if rank == best_rank:
            winners.append(PlayerList.index(p))#Adding index of winner to list
            best_rank = rank
            #To get the class of the victory to print
            rank_class = evaluator.get_rank_class(rank)
            class_string = evaluator.class_to_string(rank_class)
        elif rank < best_rank:
            winners = [PlayerList.index(p)]
            best_rank = rank
            #To get the class of the victory to print
            rank_class = evaluator.get_rank_class(rank)
            class_string = evaluator.class_to_string(rank_class)
            
    dividePot(winners)

    if len(winners) == 1:
        #Will print usernames eventually
        print 'Player x wins with %s' % class_string
    else:
        print 'Players x and y win with %s' % class_string
    

def Bets(startingPlayer, startingAmount, board):
    turn = startingPlayer
    toPay = startingAmount

    for p in PlayerList:
        p.madeMoveThisTurn = False

    roundOver = False
    while(not(roundOver)):
        move = '1' #Initialize value in case of fold
        if(PlayerList[turn].hasFolded):
            None
        elif not((PlayerList[turn].madeMoveThisTurn)):
            
            if board:
                Card.print_pretty_cards(board)
            Card.print_pretty_cards(PlayerList[turn].hand)
            
            if PlayerList[turn].chipsInPotThisTurn < toPay:
                print 'Pot size is: %d. Call %d to stay in. You have %d remaining chips' % (TotalPot(), toPay - PlayerList[turn].chipsInPotThisTurn, PlayerList[turn].chips) 
                move = raw_input('Fold (F), Call (C), or Raise (R)? ')
            else:
                print 'Pot size is: %d. You have %d remaining chips' % (TotalPot(), PlayerList[turn].chips)
                move = raw_input('Fold (F), Check (C), or Bet (B)? ')
            PlayerList[turn].madeMoveThisTurn = True
        else:
            if PlayerList[turn].chipsInPotThisTurn < toPay:
                if board:
                    Card.print_pretty_cards(board)
                Card.print_pretty_cards(PlayerList[turn].hand)
                print 'Pot size is: %d. Call %d to stay in. You have %d remaining chips' % (TotalPot(), toPay - PlayerList[turn].chipsInPotThisTurn, PlayerList[turn].chips)
                move = raw_input('Fold (F), Call (C), or Raise (R)? ')
            else:
                roundOver = True  #If player has already moved, but has nothing to bet
                                       #Then the round is neccesarily over
        if move == 'F':
            PlayerList[turn].hasFolded = True
            roundOver = LastFolded()
        elif move == 'C':
            #TestAmount = toPay-PlayerList[turn].chipsInPot
            #print 'ToPay is %d, chips is %d' % (toPay, PlayerList[turn].chipsInPot)
            PlayerList[turn].bet(toPay-PlayerList[turn].chipsInPotThisTurn)
        elif move == 'R':
            print 'The current bet is %d.' % toPay
            increase = input('How much do you want to raise? ')
            toPay += increase - (toPay - PlayerList[turn].chipsInPotThisTurn)
            PlayerList[turn].bet(increase)
        elif move == 'B':
            increase = input('How much do you want to bet? ')
            toPay += increase
            PlayerList[turn].bet(increase)
            
        turn = (turn+1)%numPlayers
    #To let the dealer know if the round has ended
    for p in PlayerList:
        p.chipsInPotThisTurn = 0
        
    if LastFolded():
        return True
    else:
        return False

def ResetHands():
    for p in PlayerList:
        p.newHand()

#Simulates a single hand
def DealHand(DEALER_TOKEN):
    
    handOver = False #True when all but one folds
    deck = Deck()

    Blinds(DEALER_TOKEN)
 
    for p in PlayerList: #As these are drawn, send to players
        p.hand = deck.draw(2)

    board = []
    handOver = Bets(((DEALER_TOKEN+3)%numPlayers), LARGE_BLIND_AMOUNT, board)

    if not(handOver):
        board = deck.draw(3)
        handOver = Bets(((DEALER_TOKEN+1)%numPlayers), 0, board)

    if not(handOver):
        board.append(deck.draw(1))
        handOver = Bets(((DEALER_TOKEN+1)%numPlayers), 0, board)

    if not(handOver):
        board.append(deck.draw(1))
        handOver = Bets(((DEALER_TOKEN+1)%numPlayers), 0, board)

    if handOver:
        FoldVictory()
    else:
        RankedVictory(board)

    ResetHands()

#Returns true if only one player has chips left
def isGameOver():
    total = 0
    for p in PlayerList:
        if p.chips > 0:
            total += 1

    if total == 1:
        return True
    else:
        return False
    
#Simulates an entire game
def Dealer():
    DEALER_TOKEN = 0
    gameOver = False
    while not(gameOver):
        #Add Players
        DEALER_TOKEN = (DEALER_TOKEN+1)%numPlayers
        DealHand(DEALER_TOKEN)
        gameOver = isGameOver()

Dealer()
         
#for p in PlayerList:
#    Card.print_pretty_cards(p.hand)
#    print 'PlayerNum: %d chips: %d Chips in pot: %d' % (PlayerList.index(p), p.chips, p.chipsInPot)
    

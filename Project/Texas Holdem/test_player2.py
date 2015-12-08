import Player

player2 = Player("username2") # Create another instance of the Player class with a different username
player2.find_game(8000) # Specify the port of the server to find an open table
                        # NOTE: The optional parameter host can be specified find_game(8000, host_to_connect_to)
                        #       If no host is specified, it defaults to the local machine


player2.cash_out(10) # players can cash out when they are not in a game
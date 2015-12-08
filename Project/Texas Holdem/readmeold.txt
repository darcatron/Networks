README:
  Overiew:
    We developed a peer to peer poker game. Users will be able to connect to a server and join a peer hosted poker table of up to 5 players.
  Functionality:
    -Server recognizes new users and keeps track of old user's info
    -Server is able to find open tables for players
    -Server allows users to "cash out" and return their chips for dollars (dollars aren't tracked)
    -Server allows users to "buy chips" and use dollars to get more chips (dollars aren't tracked)
    -Server uses update protocol to keep track of tables
      -Main peer updates server each round on the number of players in the table and the number of chips each player has 
      -If main peer disconnects, each peer updates server of disconnection and server removes table from its database. This is in case more than one peer disconnects, the server is going to get the alert from someone.
      -If peer disconnects, main peer treats it as a "fold" move for the round and removes the player from its data (server is updated about the empty seat at the end of the round)
      -If the table is not full, and everyone at the table disconnects at the same time then the server will learn about this when a new user attempts to connect to this table. If a new user cannot connect to a table host, the server will remove that table from its database and 
      
  Testing it out:
    -refer to test_server.py, test_player1.py, and test_player2.py
    -Users create a new Player class with their username
    -Players can then run Player.find_game(port_num, server_name) with a port number and server name 
  Limitations:
    -If the entire game goes down (all people in the table disconnect), then the server has no way of knowing since no one can enter (full table) and no one would tell the server that peers disconnected. 
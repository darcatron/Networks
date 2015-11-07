import socket


class Player:
    """Information about a player connection and game"""
    num_players = 0

    def __init__(self, name):
        self.name = name
        # initialize other details
        

s = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 9000                 # Reserve a port for our service.
s.bind((host, port))        # Bind to the port

s.listen(5)                 # Now wait for client connection.
while True:
   c, addr = s.accept()     # Establish connection with client.
   print 'Got connection from', addr
   c.send('Thank you for connecting')
   c.close()                # Close the connection
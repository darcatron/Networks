class Server(object):
    """
    Server that adds players to games
     maintains user information
    """
    def __init__(self):
        self.users = []
        self.tables = []

    def create_new_table(self):
        pass

    def create_new_user(self, username):
        pass

    def get_open_table(self, username):
        # TODO: 
        # if new username
        #   create_new_user
        # else
        #   if user is first player
        #      user will be the "server"
        #      send user a port they should start the "server" on and keep track of it
        #   else
        #       return ip and port of peer who is the "server"
        # TODO: look into struct library to pack and send data
        pass

    def cash_out(self):
        pass



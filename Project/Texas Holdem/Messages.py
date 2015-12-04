class Messages(object):
    
    def __init__(self):
        
        self.ID = None
        
        self.table_cards = []

        self.hand_cards = []

        self.chips_left = None

        self.chips_in_pot = None
        
    def pack(self, ID, TC, HC, CL, CIP):
        self.ID = ID
        self.table_cards = TC
        self.hand_cards = HC
        self.chips_left = CL
        self.chips_in_pot = CIP

class Print_Messages(object):

    def __init__(self):

        self.ID = 

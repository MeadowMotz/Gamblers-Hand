import secrets

PROMPT="\n".join(["----------------------------", 
                 "- /exit",
                 "- /register max prof dex",
                 "- /deal # n/h (new/held)",
                 "- /hand",
                 "- /score",
                 "- /syntax",
                 "(\'menu\' within commands to return here)",
                 "----------------------------"])
SYNTAX="\n".join(["* = joker (wild)",
                  "X = critical joker (max die damage; from rank nat 20)",
                  "- = no card/empty (from rank nat 1)"])
HEART="♥️"
iHEART=1
DIAMOND="♦️"
iDIAMOND=2
CLUB="♣️"
iCLUB=3
SPADE="♠️"
iSPADE=4
user_hold = None
user_prof = None
user_dex = None
user_max = None
registered = False
last_played = []
scored = False

# Main functions
# -------------------------
def deal(
        num_cards: int = user_max,
        type: str = False
    ):
    global user_max, user_hold, last_played, scored
    # Roll dice for cards
    rolls = []

    for i in range(num_cards):
        rank, crit = roll(20, False)
        suit, dummy = roll(4)
        rolls.append(Card(rank, suit, crit))
    
    msg:str = "Rolls: "
    i = 0
    for card in rolls:
        i = i+1
        msg += card.str()
        if not i>=len(rolls):
            msg += ", "

    if type:
        msg += "\nHold: "
        if user_hold is not None:
            for card in user_hold:
                i = i+1
                msg += card.str() + ", "
            msg = cut(msg)
        else:
            msg += "-"
            type = False
    
    # Get held and played cards
    msg += "\nr#"
    if type:
        msg += ", h#"
    msg += " -- separated by commas; #, 0 (none), a (all), or r (rest)"
    print(msg)

    def proc_choices(choices, hist, target, h_flag:bool, prev_hist = None):
        global user_hold
        nonlocal msg, type, rolls
        out:str = ""
        def proc_c(c:str, rest:bool=None):
            nonlocal msg, out, h_flag, type, prev_hist, rolls
            global user_hold
            skip = False
            if c in hist or (prev_hist is not None and c in prev_hist):
                if rest is not None and rest:
                    return
                else:
                    msg = f"!: Already held {c}"
                    raise TypeError(msg)
            elif len(c)>2:
                msg = f"!: Choice \'{c}\' is too long"
                raise TypeError(msg)
            x = c[0]
            y = None
            try:
                y = int(c[1:])
            except:
                msg = "!: Invalid syntax (#/a)"
                raise TypeError(msg)
            if x=='r':
                if y-1 in range(len(rolls)):
                    temp = rolls[y-1]
                    if h_flag or not temp.rank>=20 and not temp.rank<=1:
                        target.append(rolls[y-1])
                        out += rolls[y-1].str()
                    elif rest is None:
                        msg = "!: Cannot hold jokers (" + temp.str() + ")"
                        raise TypeError(msg)
                    else:
                        skip = True
                else:
                    msg = "!: Invalid syntax (#)"
                    raise TypeError(msg)
            elif x=='h':
                if user_hold is None and type:
                    msg = "!: Incorrect deal type or no hold"
                    raise TypeError(msg)
                if y-1 in range(len(user_hold)):
                    temp = user_hold[y-1]
                    if h_flag or not temp.rank>=20 and not temp.rank<=1:
                        target.append(user_hold[y-1])
                        out += user_hold[y-1].str()
                    else:
                        msg = "!: Cannot hold jokers (" + temp.str() + ")"
                        raise TypeError(msg)
                else:
                    msg = "!: Invalid syntax (#)"
                    raise TypeError(msg)
            if not skip:
                hist.append(c)
                out += ", "
        for choice in choices:
            if choice[0]=='0':
                if len(choices)>1:
                    msg = "!: Invalid syntax (non-solitary 0)"
                    raise TypeError(msg)
                else:
                    out = "-"
            elif len(choice)!=2:
                msg = "!: Invalid arg"
                raise TypeError(msg)
            elif choice[1]=='a' or choice[1]=='r':
                i = 0
                rest:bool = False
                if choice[1]=='r':
                    rest = True
                if choice[0]=='r':
                    i = len(rolls)
                elif choice[0]=='h':
                    if user_hold is None and type:
                        msg = "!: Incorrect deal type or no hold"
                        raise TypeError(msg)
                    else: 
                        i = len(user_hold)
                else:
                    msg = "!: Invalid syntax (r/h)"
                    raise TypeError(msg)
                for i in range(i):
                    proc_c(choice[0]+str(i+1), rest)
            else:
                proc_c(choice)
        return cut(out) # remove tailing comma
    
    choices = []
    success: bool = False
    held = []
    h_out:str
    while not success:
        msg = "!: Unknown"
        h_out = ""
        choices = []
        held = []
        while len(choices)<1 or len(choices)>user_max:
            choices = str.split(input("To hold: "), ", ")
            if choices[0]=="menu":
                return "", last_played
            if len(choices)<1 or len(choices)>user_max:
                print(f"!: You can only hold up to {user_max} cards.")
        try:
            h_hist = []
            h_out = "Held: " + proc_choices(choices, h_hist, held, False)
            if len(held)>user_max:
                msg = f"!: Trying to hold {len(held)-user_max} too many cards"
                raise ValueError(msg)
            success = True
        except:
            print(msg)  

    success = False
    r_out:str
    played = []
    while not success:
        msg = "!: Unknown"
        r_out = ""
        choices = []
        played = []
        while len(choices)<1 or len(choices)>user_max:
            choices = str.split(input("To play: "), ", ")
            if choices[0]=="menu":
                return "Returned", last_played
            if len(choices)<1 or len(choices)>user_max:
                print(f"!: You can only play up to {user_max} cards.")
        try:
            r_hist = []
            r_out = "Played: " + proc_choices(choices, r_hist, played, True, h_hist)
            if len(played)>user_max:
                msg = f"!: Trying to play {len(played)-user_max} too many cards"
                raise ValueError(msg)
            success = True
        except:
            print(msg) 
    
    user_hold = held
    scored = False
    return h_out+"\n"+r_out, played
    
def register(
    max: int,
    prof: int,
    dex: int
    ):
    global user_hold, user_prof, user_dex, user_max, registered
    rewrite = user_hold is not None
    msg = ""
    if max<1:
        msg = "!: Max hand size cannot be negative"
    else:
        user_max = max
        user_prof = prof
        user_dex = dex
        if rewrite:
            user_hold = []
            msg = "Wrote stats and hold"
        else:
            msg = "Successfully registered"
        registered = True
    return msg 

def hand():
    global user_hold
    result = "Hold: "
    if user_hold is not None:
        for card in user_hold:
            result += card.str() + ", "
        result = cut(result)
    else:
        result += "-"
    return result

def score():
    def list_played(arg):
        result = ""
        for card in arg:
            result += card.str() + ", "
        return cut(result)
    def note(card:Card):
        global iHEART, iDIAMOND, iCLUB, iSPADE
        suit = card.suit
        rank = card.rank
        if rank>=20:
            return "*", 0
        elif suit==iHEART:
            return "thp", 1
        elif suit==iDIAMOND:
            return "AC", 2
        elif suit==iCLUB:
            return "adv", 3
        elif suit==iSPADE:
            return "die+", 4
        else:
            raise ValueError("Invalid suit num")
            
    global scored, registered, last_played, iSPADE
    if not registered:
        return "!: Not registered"
    if last_played is None or len(last_played)==0:
        return "!: No cards to score"

    stack = []
    user_hand = "Cards:        " + list_played(last_played)
    notes = "Notes:        "
    dice = "Hit dice:     "
    atk = "Attack rolls: "
    dmg = "Damage:       "
    crit = False
    i = 0
    for card in last_played:
        flag = 0
        if not crit:
            crit = card.crit
        c_note, flag = note(card)
        notes += c_note + ", "
        dice += str(die(card.rank, flag)) + ", "
        atk_roll, c = roll(20, True, flag)
        if c:
            c = "*"
        else:
            c = ""
        atk += str(atk_roll) + c + ", "
        dmg_roll, dummy = roll(die(card.rank, flag))
        dmg += str(dmg_roll) + ", "
        i = i + 1
    if crit:
        crit = "Crit!"
    else:
        crit = ""

    scored = True
    return cut(user_hand) + "\n" + cut(notes) + "\n" + cut(dice) + "\n" + cut(atk) + "\n" + cut(dmg) + "\n" + crit

# Helper functions
# ------------------------
def roll(die:int, type:bool = None, flag:int = 0):
    def roll_one():
        nonlocal die, type, flag
        global user_dex, user_prof
        result:int = secrets.randbelow(die)+1
        if die==20: 
            crit:bool = False
            if result==20:
                    crit = True
            if type is None: 
                return result, crit
            elif type: # attack
                return result+user_dex, crit
            else: # rank
                return result+user_prof, crit
        return result, None
    if flag>0 and flag==3:
        r1, crit = roll_one()
        if crit: return r1, crit
        r2, crit = roll_one()
        if crit: return r2, crit
        if r1>r2: return r1, crit
        elif r2>r1: return r2, crit
        else: return r1, crit
    else:
        return roll_one()

def rank(num:int):
    result: str
    if num<1:
        raise(IndexError)
    elif num<=1:
        result = "-"
    elif num<=10:
        result = str(num)
    elif num<=12:
        result = "J"
    elif num<=14:
        result = "Q"
    elif num<=16:
        result = "K"
    elif num<=19:
        result = "A"
    elif num==20:
        result = "X"
    else:
        result = "*"
    return result

def cut(s:str): # remove ", " 
    if s[-2:]==", ":
        return s[:(len(s)-2)]
    else:
        return s

def suit(num:int):
    global iHEART, iDIAMOND, iCLUB, iSPADE
    result: str
    if num==iHEART:
        result = HEART
    elif num==iDIAMOND:
        result = DIAMOND
    elif num==iCLUB:
        result = CLUB
    elif num==iSPADE:
        result = SPADE
    else:
        raise TypeError(f"Invalid suit number: {num}")
    return result

def die(rank:int, flag):
    if rank<2:
        result = 0
    elif rank<11:
        result = 4
    elif rank<17:
        result = 6
    elif rank<20:
        result = 8
    else:
        result = 10
    if flag==4 and not rank<2:
        result += 2
    return result

class Card():
    rank:int
    suit:int
    crit:bool
    def __init__(self, rank:int, suit:int, crit:bool = False):
        self.rank = rank
        self.suit = suit
        self.crit = crit

    def str(self):
        r = rank(self.rank)
        s = suit(self.suit)
        if self.crit:
            r = "X"
        if r=="*" or r=="X" or r=="-":
            s = ""
        return s + r
    
# Main
# -------------------
finish = False
while not finish:
    msg:str = ""
    print(PROMPT)
    cmd = input("> ")
    args = str.split(cmd[1:],' ')
    if cmd[0]=='/':
        cmd = cmd[1:]
        if args[0]=="exit":
            msg = "Exiting . . ."
            finish = True
        if args[0]=="syntax":
            msg = SYNTAX
        elif args[0]=="register":
            if len(args)==4 and args[1].isdecimal() and args[2].isdecimal() and args[3].isdecimal():
                msg = register(int(args[1]), int(args[2]), int(args[3]))
            else: 
                msg = "!: Wrong # or invalid args"
        elif args[0]=="deal":
            if not registered:
                msg = "!: Not registered"
            elif 1<=len(args)<=3:
                hold = True
                if len(args)>2:
                    if args[2]=="n":
                        hold = False
                    elif not args[2]=="h":
                        msg = "!: Invalid hand type"
                if len(args)>=2:
                    if not args[1].isdecimal():
                        msg = f"!: Invalid arg \'{args[1]}\'"
                    else:
                        num = int(args[1])
                    if not (1<=num and num<=user_max):
                        msg = "!: Invalid card number"
                    else:
                        msg, last_played = deal(int(args[1]), hold)
                else:
                    msg, last_played = deal(user_max, hold)
            else:
                msg = "!: Invalid syntax"
        elif args[0]=="hand":
            if not registered:
                msg = "!: Not registered"
            else:
                msg = hand()
        elif args[0]=="score":
            if not registered:
                msg = "!: Not registered"
            else:
                msg = score()
        else: 
            msg = "!: Invalid command"

    print(msg)

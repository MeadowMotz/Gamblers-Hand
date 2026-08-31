import secrets, traceback, discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='gh$ ', intents=intents)
token_file = open("../bot_token")
BOT_TOKEN = token_file.read()
token_file.close()

PROMPT="\n".join(["----------------------------",
                 "- register max prof dex",
                 "- deal # n/h (new/held)",
                 "- hand",
                 "- score",
                 "- syntax",
                 "- play \\*",
                 "- hold \\*",
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

user_hold = None
user_prof = None
user_dex = None
user_max = None
registered = False
last_played = []
scored = False
wait_hold = False
wait_play = False
hold_hist = []
last_rolls = []

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user.name}")

# Command
# -------------------------
@bot.command(name='deal')
async def deal(ctx, num_cards: int = user_max, d_type: str = 'n'):
    global user_hold, registered, wait_hold, wait_play, last_rolls

    msg = ""
    err = False
    if not registered:
        msg = "!: Not registered"
        err = True
    elif num_cards>user_max:
        msg = "!: Invalid card number"
        err = True
    elif wait_hold:
        msg = "!: Waiting for user to choose their held cards"
        err = True
    elif wait_play:
        msg = "!: Waiting for user to choose their played cards"
        err = True
    elif not (d_type=='h' or d_type=='n'):
        msg = "!: Invalid hand type"
        err = True
    if err:
        await ctx.channel.send(msg)
        return

    if d_type=='n':
        type = False
    elif d_type=='h':
        type = True
    else: raise Exception("!: Unknown")
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

    msg += "\n*Use play and hold commands to choose your cards*"
    # Get held and played cards
    msg += "\nr#"
    if type:
        msg += ", h#"
    msg += " -- separated by spaces; #, 0 (none), a (all), or r (rest)"
    await ctx.channel.send(msg)
    wait_hold = True
    wait_play = True
    last_rolls = rolls

@bot.command(name='play')
async def play(ctx, *choices):
    global wait_play, user_max, hold_hist, last_played, wait_hold

    if wait_hold:
        await ctx.channel.send("!: Choose your held cards first")
        return
    elif not wait_play:
        await ctx.channel.send("!: No dealt cards or already played")
        return
    elif len(choices)==0:
        await ctx.channel.send("!: Nothing chosen")
        return

    try:
        r_hist = []
        played = []
        r_out = "Played: " + proc_choices(choices, r_hist, played, True, hold_hist)
        if len(played)>user_max:
            raise ValueError(f"!: Trying to play {len(played)-user_max} too many cards")
        else:
            last_played = played
            await ctx.channel.send(r_out)
            wait_play = False
    except (e):
        await ctx.channel.send(e.message)

@bot.command(name='hold')
async def hold(ctx, *choices):
    global wait_hold, user_max, hold_hist, user_hold

    if not wait_hold:
        await ctx.channel.send("!: No dealt cards or already held")
        return
    elif len(choices)==0:
        await ctx.channel.send("!: Nothing chosen")
        return

    try:
        h_hist = []
        held = []
        h_out = "Held: " + proc_choices(choices, h_hist, held, False)
        if len(played)>user_max:
            raise ValueError(f"!: Trying to hold {len(held)-user_max} too many cards")
        else:
            user_hold = held
            await ctx.channel.send(h_out)
            wait_hold = False
            hold_hist = h_hist
    except Exception as e:
        await ctx.channel.send(str(e))
        traceback.print_exc()

@bot.command(name='register')
async def register(ctx, max: int, prof: int, dex: int):
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
            msg = f"Successfully registered (Max: {user_max}, Prof: {user_prof}, Dex: {user_dex})"
        registered = True
    await ctx.channel.send(msg)

@bot.command(name='hand')
async def hand(ctx):
    global user_hold, registered
    if not registered:
        await ctx.channel.send("!: Not registered")
        return
    result = "Hold: "
    if user_hold is not None:
        for card in user_hold:
            result += card.str() + ", "
        result = cut(result)
    else:
        result += "-"
    await ctx.channel.send(result)

@bot.command(name='score')
async def score(ctx):
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
    msg = ""
    err = False
    if not registered:
        msg = "!: Not registered"
        err = True
    elif last_played is None or len(last_played)==0:
        msg = "!: No cards to score"
        err = True
    elif wait_hold:
        msg = "!: Waiting for user to choose their held cards"
        err = True
    elif wait_play:
        msg = "!: Waiting for user to choose their played cards"
        err = True
    if err:
        await ctx.channel.send(msg)
        return

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
    await ctx.channel.send(cut(user_hand) + "\n" + cut(notes) + "\n" + cut(dice) + "\n" + cut(atk) + "\n" + cut(dmg) + "\n" + crit)

@bot.command(name='syntax')
async def syntax(ctx):
    await ctx.channel.send(PROMPT + "\n" + SYNTAX)

@bot.command(name='discard')
async def discard(ctx):
    global wait_hold, wait_play
    wait_hold = False
    wait_play = False
    await ctx.channel.send("Discarded previous rolls")

# Helper functions
# ------------------------
def proc_choices(choices, hist, target, h_flag:bool, prev_hist = None):
    global user_hold, wait_hold, last_rolls
    out:str = ""
    def proc_c(c:str, rest:bool=None):
        nonlocal out, h_flag, prev_hist
        global user_hold, last_rolls
        skip = False
        if c in hist or (prev_hist is not None and c in prev_hist):
            if rest is not None and rest:
                return
            else:
                raise TypeError(f"!: Already held {c}")
        elif len(c)>2:
            raise TypeError(f"!: Choice \'{c}\' is too long")
        x = c[0]
        y = None
        try:
            y = int(c[1:])
        except:
            raise TypeError("!: Invalid syntax (#/a)")
        if x=='r':
            if y-1 in range(len(last_rolls)):
                temp = last_rolls[y-1]
                if h_flag or not temp.rank>=20 and not temp.rank<=1:
                    target.append(last_rolls[y-1])
                    out += last_rolls[y-1].str()
                elif rest is None:
                    raise TypeError("!: Cannot hold jokers (" + temp.str() + ")")
                else:
                    skip = True
            else:
                raise TypeError("!: Invalid syntax (#)")
            if y-1 in range(len(user_hold)):
                temp = user_hold[y-1]
                if h_flag or not temp.rank>=20 and not temp.rank<=1:
                    target.append(user_hold[y-1])
                    out += user_hold[y-1].str()
                else:
                    raise TypeError("!: Cannot hold jokers (" + temp.str() + ")")
            else:
                raise TypeError("!: Invalid syntax (#)")
        if not skip:
            hist.append(c)
            out += ", "
    for choice in choices:
        if choice[0]=='0':
            if len(choices)>1:
                raise TypeError("!: Invalid syntax (non-solitary 0)")
            else:
                out = "-"
        elif len(choice)!=2:
            raise TypeError("!: Invalid arg")
        elif choice[1]=='a' or choice[1]=='r':
            i = 0
            rest:bool = False
            if choice[1]=='r':
                rest = True
            if choice[0]=='r':
                i = len(last_rolls)
            elif choice[0]=='h':
                if user_hold is None and wait_hold:
                    raise TypeError("!: Incorrect deal type or no hold")
                else:
                    i = len(user_hold)
            else:
                raise TypeError("!: Invalid syntax (r/h)")
            for i in range(i):
                proc_c(choice[0]+str(i+1), rest)
        else:
            proc_c(choice)
    return cut(out) # remove tailing comma

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

# Main
# -------------------
bot.run(BOT_TOKEN)

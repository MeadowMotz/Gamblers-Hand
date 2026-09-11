import secrets, traceback, discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button
from typing import List

# Classes
# -------------------------
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

# class DealPlay(discord.ui.View):
#     @discord.ui.button(style=discord.ui.ButtonStyle.green, emoji="⚔️", label="Play")
#     async def callback(self, interact:discord.Interaction):
#         pass
#
# class DealDiscard(discord.ui.View):
#     @discord.ui.button(style=discord.ui.ButtonStyle.red, emoji="🗑️", label="Disard")
#     async def callback(self, interact:discord.Interaction):
#         pass

# deal response template
class DealEmbed(discord.Embed):
    r_drops = []
    h_drops = []

    def __init__(self, rolls:List[Card], deal_type:bool):
        global user_hold
        super().__init__(color=discord.Colour.orange(), title="Choose your cards")
        self.add_field(name="Rolls: ", value="", inline=False)
        for card in rolls:
            r_sel = Select(options=["Hold", "Play"], placeholder="Discard")
            self.r_drops.append(r_sel)
            self.add_field(r_sel, name=card.str(), value="")

        if deal_type:
            self.add_field(name="Held: ", inline=False)
            if user_hold is not None:
                for card in user_hold:
                    h_sel = Select(options=["Hold", "Play"], placeholder="Discard")
                    self.h_drops.append(h_sel)
                    self.add_field(h_sel, name=card.str(), value="")

            for i in user_max-len(user_hold):
                self.add_field(name="-", value="")

        return
        # self.add_field(DealPlay(), inline = False)
        # self.add_field(DealDiscard())
        #TODO callbacks


class Client(commands.Bot):
    async def on_ready(self):
        result = await self.tree.sync(guild=self.get_guild(1342165798780669972))
        if result is not None and len(result)>0:
            msg = f"[GH$] Synced {len(result)} commands: "
            for i in result:
                msg += i.name + ", "
            print(cut(msg))

        print("[GH$] Ready for another round!")

# Discord setup & main
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = Client(command_prefix="gh$ ", intents=intents)
token_file = open("../bot_token")
BOT_TOKEN = token_file.read()
token_file.close()

bot.run(BOT_TOKEN)

# Backend variables
# -------------------------
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

# Events
# -------------------------
# error logging
@bot.listen('on_command_error')
async def cmd_err_handle(ctx, exc:Exception):
    e = traceback.format_exception(exc)
    stacktrace = ""
    for i in e:
        stacktrace += i
    print("[ERROR] " + stacktrace)
    log = open("./err_log.txt","w")
    log.write(stacktrace)
    log.close()
    await ctx.reply(embed=discord.Embed(colour=discord.Colour.red(), title="Error!", description="Outputted to log file."), mention_author=True, delete_after=60.0)

# Commands
# -------------------------
# roll new hand of cards to choose from
@bot.command(name='deal')
async def deal(ctx, num_cards: int = user_max, deal_type: bool = True):
    global user_hold, registered, wait_hold, wait_play, last_rolls

    # Error checking
    msg = ""
    err = False
    if not registered:
        msg = "!: Not registered"
        err = True
    elif num_cards is None or deal_type is None:
        msg = "!: Missing arg"
        err = True
    elif num_cards>user_max:
        msg = "!: Invalid card number"
        err = True
    if err:
        await ctx.reply(embed=discord.Embed(colour=discord.Colour.red(), description=msg), delete_after=60.0, mention_author=True)
        return

    # Roll dice for cards
    rolls = []
    for i in range(num_cards):
        rank, crit = roll(20, False)
        suit, dummy = roll(4)
        rolls.append(Card(rank, suit, crit))

    await ctx.reply(embed=DealEmbed(rolls=rolls, deal_type=deal_type), mention_author=True)
'''
#TODO
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
'''
# load user stats for roll modifiers (spell reqs)
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
'''
# print user hold/hand
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

# score chosen cards, auto rolling
@bot.command(name='score')
async def score(ctx):
    def list_played(arg):
        result = ""
        for card in arg:
            result += card.str() + ", "
        return cut(result)
    def note(card:Card): # decode suit effect (spell reqs)
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
    # context validation
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
        atk_roll, c = roll(20, True, flag) # make attack roll
        if c: # crit flag in output
            c = "*"
        else:
            c = ""
        atk += str(atk_roll) + c + ", "
        dmg_roll, dummy = roll(die(card.rank, flag)) # make dmg roll
        dmg += str(dmg_roll) + ", "
        i = i + 1
    if crit:
        crit = "Crit!"
    else:
        crit = ""

    scored = True
    await ctx.channel.send("\n".join(cut(user_hand), cut(notes), cut(dice), cut(atk), cut(dmg), crit))

@bot.command(name='syntax')
async def syntax(ctx):
    await ctx.channel.send(PROMPT + "\n" + SYNTAX)

@bot.command(name='discard')
async def discard(ctx):
    global wait_hold, wait_play
    wait_hold = False
    wait_play = False
    await ctx.channel.send("Discarded previous rolls")

'''
# Helper functions
# ------------------------
# add user [type:play|hold] choices to globals, with input validation
# checks against already processed choices for duplicates
# TODO read for bugs
def proc_choices(choices, hist, target, h_flag:bool, prev_hist = None):
    global user_hold, wait_hold, last_rolls
    out:str = ""
    def proc_c(c:str, rest:bool=None):
        nonlocal out, h_flag, prev_hist
        global user_hold, last_rolls
        skip = False
        # validate against current and previous (same roll set) choice history
        if c in hist or (prev_hist is not None and c in prev_hist):
            if rest is not None and rest:
                return
            else:
                raise TypeError(f"!: Already held {c}")
        elif len(c)>2:
            raise TypeError(f"!: Choice \'{c}\' is too long")
        x = c[0] # parse roll type source (rolls or hold)
        y = None
        try:
            y = int(c[1:])
        except:
            raise TypeError("!: Invalid syntax (#/a)")

        if x=='r': # pull from rolls in set
            if y-1 in range(len(last_rolls)):
                temp = last_rolls[y-1] # adjust 1- to 0- index
                if h_flag or not temp.rank>=20 and not temp.rank<=1:
                    target.append(temp)
                    out += temp.str()
                elif rest is None:
                    raise TypeError("!: Cannot hold jokers (" + temp.str() + ")") # (spell reqs)
                else:
                    skip = True
            else:
                raise TypeError("!: Invalid syntax (#)")

        # TODO logic bug, missing hold type case
            if y-1 in range(len(user_hold)):
                temp = user_hold[y-1]
                if h_flag or not temp.rank>=20 and not temp.rank<=1:
                    target.append(temp)
                    out += temp.str()
                else:
                    raise TypeError("!: Cannot hold jokers (" + temp.str() + ")")
            else:
                raise TypeError("!: Invalid syntax (#)")
        if not skip:
            hist.append(c)
            out += ", "


    for choice in choices:
        if choice[0]=='0': # choice skip check
            if len(choices)>1:
                raise TypeError("!: Invalid syntax (non-solitary 0)")
            else:
                out = "-"
        elif len(choice)!=2:
            raise TypeError("!: Invalid arg")
        elif choice[1]=='a' or choice[1]=='r': # loop choice options for all or rest
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
        else: # normal [type][index] choice
            proc_c(choice)
    return cut(out)

# random dice rolling of [die] size
# adjusts for roll [type:attack|rank|flat] based on type and handles advantage
def roll(die:int, type:bool = None, flag:int = 0): #
    def roll_one():
        nonlocal die, type, flag
        global user_dex, user_prof
        result:int = secrets.randbelow(die)+1 # adjust from 0- to 1- index

        # add user stats (spell reqs)
        if die==20:
            crit:bool = False
            if result==20:
                    crit = True
            if type is None: # flat roll
                return result, crit
            elif type: # attack roll
                return result+user_dex, crit
            else: # rank roll
                return result+user_prof, crit
        return result, None

    # choose higher (roll w/ advantage)
    if flag>0 and flag==3:
        r1, crit = roll_one()
        if crit: return r1, crit
        r2, crit = roll_one()
        if crit: return r2, crit

        if r1>r2: return r1, crit
        elif r2>r1: return r2, crit
        else: return r1, crit # same roll
    else:
        return roll_one()

# decode card rank from rolled int
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

# remove ", "
def cut(s:str):
    if s[-2:]==", ":
        return s[:(len(s)-2)]
    else:
        return s

 # decode card suit from rolled int
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

# determine die size from card rank (spell reqs)
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

from typing import final
import discord
import re
import random
import config

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

'''
Game states:
0 - No current game
1 - Game has been created but not started
2 - Game is running
'''

'''
Commands:
createGame - Sets gamestate to 1
quitGame - Sets gamestate to 0
startgame - set gamestate to 2 if there are enough players
join - joins the current game if it is active
bet - 
'''

gameState = 0
gameStarted = 0
players = {}
turn = ""
lastBet = [0, 0]
lastTurn = ""
finalCount = [0,0]

@client.event
async def on_ready():
    global gameState
    gameStarted = 0
    global players
    players = {

    }
    global turn
    turn = ""
    global lastBet
    lastBet = [0,0]
    global lastTurn
    lastTurn = ""
    global gameChannel
    global finalCount
    finalCount = [0,0]

@client.event
async def on_message(message):
    global gameState
    global lastBet
    global turn
    global lastTurn
    global players
    global gameChannel

    if(message.content.startswith('ld! ') ): #all commands begin with a ld!
        if (message.content).strip().lower() == ('ld! create'):
            if gameState == 0: #change gamestate to created if not
                gameState = 1
                await message.channel.send("A game has been created.")
                gameChannel = message.channel

        elif (message.content).strip().lower() == ('ld! quit'):
            if gameState == 1: #change gamestate to None if one is created
                gameState = 0
                await message.channel.send("Game was quit.")
                clearVars()

        elif (message.content).strip().lower() == ('ld! current'):
            if gameState == 1:
                await message.channel.send("There is already a created game.")
            elif gameState == 2:
                await message.channel.send("A game is currently in progress.")
            else:
                await message.channel.send("No games are currently being played.")

        elif (message.content).strip().lower() == ('ld! join'):
            if gameState == 1:
                if not players.keys().__contains__(message.author.name):
                    players[message.author.name] = []
                    await message.channel.send(message.author.name + " joined the game.")
                else:
                    await message.channel.send("You are already in the game.")
            elif gameState == 2:
                await message.channel.send("You can't join in the middle of a game.")
            else:
                await message.channel.send("A game has not been created. Do 'ld! CreateGame to create one!'")

        elif (message.content).strip().lower() == ('ld! start'):
            if(gameState == 1):
                if len(list(players.keys())) >= 2:
                    gameState = 2
                    await startGame(message.channel)
                    await message.channel.send("It is " + turn + "'s turn.")
                else:
                    await message.channel.send("Not enough players to start.")
            elif(gameState == 2):
                await message.channel.send("A game is currently in progress.")
            else:
                await message.channel.send("A game has not been started. Do 'ld! CreateGame to start one!")

        elif ((message.content).strip().lower())[:7] == ('ld! bet'):
            if gameState == 2:
                if turn == message.author.name:
                    if getBet(message.content) != -1:
                        if((getBet(message.content)[0] > lastBet[0]) or (getBet(message.content)[1] > lastBet[1] and getBet(message.content)[0] == lastBet[0])):
                            lastBet = getBet(message.content)
                            lastTurn = turn
                            await message.channel.send(lastTurn + " bet " + betString(lastBet))
                            turn = nextTurn(message.author.name)
                            await message.channel.send("It is " + turn + "'s turn.")
                        else:
                            await message.channel.send("Your bet must be greater than the last bet: " + betString(lastBet))
                    else:
                        await message.channel.send("Please use two separate numbers to input your bet.")
                else:
                    await message.channel.send("It is currently " + turn + "'s turn to play.")
            elif gameState == 1:
                await message.channel.send("The game has not yet been started.")
            else:
                await message.channel.send("The game has not yet been created.")

        elif (message.content).strip().lower() == ('ld! liar'):
            if gameState == 2:
                if turn == message.author.name:
                    if(callLiar(lastBet) == 0):
                        await message.channel.send("The winner is: " + lastTurn + "\n\
There were " + betString(finalCount))
                    else:
                        await message.channel.send("The winner is: " + message.author.name+ "\n\
There were " + betString(finalCount))
                    await printAllDice()
                    await message.channel.send("Good Game! Do 'ld! startgame' to play again!")
                    clearVars()
                else:
                    await message.channel.send("You cannot call Liar on another Player's turn.")
            elif gameState == 1:
                await message.channel.send("The game has not yet been started.")
            else:
                await message.channel.send("The game has not yet been created.")

        elif (message.content).strip().lower() == ('ld! help'):
            await message.channel.send("All commands begin with a 'ld!'\n\
Create - Creates a new lobby for a game of Liar's Dice.\n\
Start - Starts the game.\n\
Quit - Quits the game.\n\
Join - Joins the current lobby.\n\
Bet - Bet the number of dice(Input two separate numbers).\n\
Liar - Call the last player a Liar.\n\
Rules - View the rules of Liar's Dice.")

        elif (message.content).strip().lower() == ('ld! rules'):
            await message.channel.send("To play you must have at least two players but the recommended number is three to five.\n\
The goal is to bet a correct number of dice on the board. You get to see your five dice but you are playing everybody in the game's dice when you bet. Player's bet in order until someone calls 'Liar.'\n\
A player can only call 'Liar' on the bet that happened the turn before their turn. If 'Liar' is called, the dice are counted and if the number of dice is less than or equal to the bet number, the player who was called a Liar wins. If the number of dice is greater, the player who called Liar wins.\n\
Bets must be increased by the number on the die, or by the number of dice. For example, 2 4s can be bet on by 3 3s or 2 6s but not by 1 6")
        
        elif (message.content).strip().lower() == ('ld! currentbet'):     
            if gameState == 2:
                if lastBet != [0,0]:
                    await message.channel.send("The current bet is: " + betString(lastBet))
        elif (message.content).strip().lower() == ('ld! leave'):
            playerIn = players.pop(message.author.name,0)
            if playerIn == 0:#player not in
                await message.channel.send(message.author + " not found in the game.")
            else:
                await message.channel.send(message.author + " removed from the game.")
        else:
            await message.channel.send("Unknown command. Do ld! help for a list of Liar's Dice commands.")

def betString(bet):
    return(str(bet[0]) + " " + intString(bet[1]))

def intString(num):
    numArray = ["one","two", "three", "four", "five", "six"]
    if num < 6:
        return str(numArray[num-1]) + "s"
    else:
        return str(numArray[num-1]) + "es"

def getBet(betInput):

    matches = re.findall(r'\d+', betInput)

    if len(matches) == 2 and int(matches[1]) > 0 and int(matches[1]) < 7:
        retBet = [int(matches[0]), int(matches[1])]
        return(retBet)
    else:
        return(-1)
        #print("Please use two numbers with a space in between to input your bet.")

def nextTurn(currTurn):
    global players

    player_names = list(players.keys())
    num_players = len(player_names)

    # Find the current player's index
    try:
        curr_index = player_names.index(currTurn)
    except ValueError:
        return None  # Player not found in the dictionary

    # Calculate the index of the next player (wrapping around if needed)
    next_index = (curr_index + 1) % num_players

    return player_names[next_index]

def callLiar(bet):

    global players
    global finalCount

    totCount = 0

    numberOfDice = bet[0]
    numberOnDice = bet[1]

    #print("Number " + str(numberOfDice))
    #print("Die " + str(numberOnDice))

    for values in players.values():
        count = 0
        for diceNum in values:
            if diceNum == numberOnDice:
                count = count +1
        totCount = totCount + count

    finalCount[0] = totCount
    finalCount[1] = numberOnDice
    
    if totCount <= numberOfDice: #0 means not a lie, 1 means liar
        return 0
    else:
        return 1
    
async def printAllDice():

    global players

    printString = ""
    for item in players:
        printString = printString + item + ": " + getDice(players[item]) + "\n"

    await gameChannel.send(printString)
        

async def startGame(channelName):

    global players
    global turn

    for item in players.keys():
        players[item] = rollDice()
        playerName = discord.utils.get(channelName.guild.members, name=item)

        await playerName.send("Your rolls are: " + getDice(players[item]))
    
    turn = (list(players.keys()))[0]


def getDice(diceList):
    retString = ""
    for die in diceList:
        retString = retString + str(die) + " "

    return retString

def rollDice():
    return[random.randint(1,6),random.randint(1,6),random.randint(1,6),random.randint(1,6),random.randint(1,6)]

def clearVars():

    global gameChannel, gameState, players, lastBet, turn, lastTurn

    gameState = 1
    turn = ""
    lastBet = [0, 0]
    lastTurn = ""
    finalCount = [0,0]

client.run(config.discord_api_key)
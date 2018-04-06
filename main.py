from flask import Flask, request
import json
from slackclient import SlackClient
import requests
import random

app = Flask(__name__)

players = {}
gameStarted = False
deck = []
liberalsPlayed = 0
fascistsPlayed = 0

def findAmountOfRoles(totalPlayers):
    roleAmounts = {}
    if(totalPlayers == 5 or totalPlayers == 6):
        roleAmounts['fascists'] = 1
    elif(totalPlayers == 7 or totalPlayers == 8):
        roleAmounts['fascists'] = 2
    elif(totalPlayers == 9 or totalPlayers == 10):
        roleAmounts['fascists'] = 3
    roleAmounts['liberals'] = totalPlayers - 1 - roleAmounts['fascists']
    return roleAmounts

def findFirstPresident(totalPlayers):
    global players
    firstPresidentId = random.randint(1,totalPlayers)
    i = 1
    for key in players:
        if(i == firstPresidentId):
            return players[key]
        i = i + 1

def sendRoles(roleAmounts,totalPlayers,slackclient):
    global players
    randomHitler = random.randint(1,totalPlayers)
    randomFascists = []
    while (len(randomFascists) is not roleAmounts['fascists']):
        randomAttempt = random.randint(1,totalPlayers)
        if(randomAttempt not in randomFascists and randomAttempt != randomHitler):
            randomFascists.append(randomAttempt)
    i = 1
    fascists = []
    hitler = ''
    for key in players:
        if(randomHitler == i):
            hitler = key
            slackclient.api_call("chat.postMessage", channel=key, text='You are Hitler.', as_user=True)
        elif(i in randomFascists):
            fascists.append(key)
        else:
            slackclient.api_call("chat.postMessage", channel=key, text='You are Liberal.', as_user=True)
        i = i + 1

    for key in fascists:
        otherFascists = fascists.copy()
        otherFascists.remove(key)
        otherFacistsForSlack = ''
        if(len(otherFascists) > 0):
            otherFacistsForSlack = 'Your other fascist(s): '
            for otherKey in otherFascists:
                otherFacistsForSlack += '|' + players[otherKey] + '| '
        facsistsMessageForSlack = 'You are Fascist.\n' + otherFacistsForSlack + '\nYour Hitler is: |' + players[hitler] + '|'
        slackclient.api_call("chat.postMessage", channel=key, text=facsistsMessageForSlack, as_user=True)

    if(totalPlayers < 7):
        slackclient.api_call("chat.postMessage", channel=hitler, text=('Your friendly fascist is: ' + players[fascists[0]]), as_user=True)


def sendPlayers(slackclient):
    global players
    playersListForSlack = 'Players:\n'
    playersNumber = 0
    for key in players:
        playersNumber = playersNumber + 1
        playersListForSlack += str(playersNumber) + '. ' + players[key] + '\n'
    slackclient.api_call("chat.postMessage", channel="CA1HP594N", text=playersListForSlack)

def shuffleDeck():
    global liberalsPlayed
    global fascistsPlayed
    global deck
    deck = []
    totalTilesLeft = 17 - liberalsPlayed - fascistsPlayed
    liberalsLeft = 6 - liberalsPlayed
    liberalTileLocations = random.sample(range(0, totalTilesLeft-1), liberalsLeft)
    for i in range(totalTilesLeft):
        if i in liberalTileLocations:
            deck.append('Liberal')
        else:
            deck.append('Fascist')

def drawDeck(slackclient,userId):
    global deck
    if(len(deck) < 3):
        shuffleDeck()
    card1 = deck.pop()
    card2 = deck.pop()
    card3 = deck.pop()
    slackclient.api_call("chat.postMessage", channel=userId, text='Choices:\n1. ' + card1 + '\n2. ' + card2 + '\n3. ' + card3, as_user=True)

def playCard(slackclient,userId,cardType):
    global players
    playCardForSlack = players[userId] + ' played a ' + cardType + ' card.'
    slackclient.api_call("chat.postMessage", channel="CA1HP594N", text=playCardForSlack)
    printBoard(slackclient)

def printBoard(slackclient):
    global deck
    global liberalsPlayed
    global fascistsPlayed

    sendPlayers(slackclient)
    liberalAmt = liberalsPlayed
    liberalsAsString = ''
    for i in range(0,5):
        if(liberalAmt > i):
            liberalsAsString += '|  X  |'
        else:
            liberalsAsString += '|       |'

    fascistAmt = fascistsPlayed
    fascistsAsString = ''
    for i in range(0,6):
        if(fascistAmt > i):
            fascistsAsString += '| X |'
        else:
            fascistsAsString += '|     |'

    boardForSlack = '.               -----------------------------' + '\n'
    boardForSlack += 'Liberals |' + liberalsAsString + '|Discard: ' + str((17-len(deck)-liberalsPlayed-fascistsPlayed)) + '\n'
    boardForSlack += '                |-----------------------------|' + '\n'
    boardForSlack += 'Fascists |' + fascistsAsString + '|Draw Pile: ' + str(len(deck)) + '\n'
    boardForSlack += '                 -----------------------------' + '\n'
    slackclient.api_call("chat.postMessage", channel="CA1HP594N", text=boardForSlack)

def peekDeck(slackclient,userId):
    global deck
    if(len(deck) < 3):
        shuffleDeck()
    card1 = deck.pop()
    card2 = deck.pop()
    card3 = deck.pop()
    deck.append(card3)
    deck.append(card2)
    deck.append(card1)
    slackclient.api_call("chat.postMessage", channel=userId, text='Top of Deck:\n1. ' + card1 + '\n2. ' + card2 + '\n3. ' + card3, as_user=True)




@app.route('/', methods=['POST'])
def slackEntryPoint():
    apiToken = 'YOURTOKEN'
    slackclient = SlackClient('YOURTOKEN')
    global players
    global gameStarted
    global liberalsPlayed
    global fascistsPlayed
    global deck
    jsonData = json.loads(request.data)

    try:
        userId = jsonData['event']['user']

        if 'bot_id' in jsonData['event']:
            return 'shhhhh'

        if(jsonData['event']['text'] == '<@UA00TD12L> create'):
            players = {}
            gameStarted = False
            liberalsPlayed = 0
            fascistsPlayed = 0
            shuffleDeck()
            gameCreateForSlack = 'You have created a new game. Please have players join. When all players have joined, run the start command.'
            slackclient.api_call("chat.postMessage", channel="CA1HP594N", text=gameCreateForSlack)

        if(jsonData['event']['text'] == '<@UA00TD12L> join' and not gameStarted):
            userurl = 'https://slack.com/api/users.info?token=' + apiToken + '&user=' + userId
            r = requests.get(userurl)
            userJson = r.json()
            if 'user' in userJson and 'real_name' in userJson['user']:
                players[userId] = userJson['user']['real_name']
            else:
                players[userId] = players[userId]
            sendPlayers(slackclient)

        if(jsonData['event']['text'] == '<@UA00TD12L> start' and not gameStarted):
            gameStarted = True
            totalPlayers = len(players)
            startMessageForSlack = 'The game is starting with ' + str(totalPlayers) + ' players.\n'
            roleAmounts = findAmountOfRoles(totalPlayers)
            startMessageForSlack += 'There will be ' + str(roleAmounts['fascists']) + ' fascists (not including Hitler) and ' + str(roleAmounts['liberals']) + ' liberals.\n'
            startMessageForSlack += 'Your roles will be DMed to you.\n'
            startMessageForSlack += 'First president will be ' + findFirstPresident(totalPlayers) + '. Please choose your first Chancellor.'
            slackclient.api_call("chat.postMessage", channel="CA1HP594N", text=startMessageForSlack)
            sendRoles(roleAmounts,totalPlayers,slackclient)

        if(jsonData['event']['text'] == '<@UA00TD12L> players'):
            sendPlayers(slackclient)

        if(jsonData['event']['text'] == '<@UA00TD12L> draw'):
            drawDeck(slackclient,userId)

        if(jsonData['event']['text'] == '<@UA00TD12L> fascist'):
            fascistsPlayed = fascistsPlayed + 1
            playCard(slackclient,userId,'fascist')

        if(jsonData['event']['text'] == '<@UA00TD12L> liberal'):
            liberalsPlayed = liberalsPlayed + 1
            playCard(slackclient,userId,'liberal')

        if(jsonData['event']['text'] == '<@UA00TD12L> board'):
            printBoard(slackclient)

        if(jsonData['event']['text'] == '<@UA00TD12L> peek'):
            peekDeck(slackclient,userId)

        if(jsonData['event']['text'].startswith('<@UA00TD12L> kill')):
            withoutStart = jsonData['event']['text'].replace('<@UA00TD12L> kill ','')
            withoutLeftJunk = withoutStart.replace('<@','')
            userToKill = withoutLeftJunk.replace('>','')
            players[userToKill] = ':skull:' + players[userToKill] + ':skull:'
            sendPlayers(slackclient)

        if(jsonData['event']['text'] == '<@UA00TD12L> commands' or jsonData['event']['text'] == '<@UA00TD12L> help'):
            helpTextForSlack = """
            Commands:
            create - Resets current game and starts a new lobby.
            join - Joins the game lobby.
            start - Starts the game and sends everyone in lobby their roles.
            draw - President uses once Chancellor is elected. The bot will pm you 3 tiles off the top of the deck.
            fascist - Plays a fascist tile.
            liberal - Plays a liberal tile.
            players - Displays the list of players.
            board - Displays the current state of the game. The board and the players list.
            peek - President uses this power on the 3rd fascist tile played in a 5/6 player game.
            kill @slackname - President uses this power to kill a player on the 4th and 5th fascist tile played.
            """
            slackclient.api_call("chat.postMessage", channel=userId, text=helpTextForSlack, as_user=True)



    except Exception as e:
        print('errorbeepboop: ' + str(e))
        slackclient.api_call("chat.postMessage", channel="UA1NF0F2B", text=str(e))
    finally:
        return 'shhhhh'

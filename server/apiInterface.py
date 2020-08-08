import json
import requests
import datetime
import time
import os.path
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, request
from PIL import Image 

#PEOPLE_FOLDER = os.path.join('..\static', 'plots')
app = Flask(__name__)
#app.config['UPLOAD_FOLDER'] = PEOPLE_FOLDER
FANTASY_SKATER_STATISTICS = ['goals', 'assists', 'pim', 'powerPlayPoints', 'shortHandedPoints', 'shots', 'hits', 'blocked']
FANTASY_GOALIE_STATISTICS = ['wins', 'goalsAgainst', 'saves', 'shutouts']
FANTASY_SKATER_SCORES = list()
FANTASY_GOALIE_SCORES = list()

def getFantasyStatistics():
  global FANTASY_SKATER_SCORES
  global FANTASY_GOALIE_SCORES
  for i in FANTASY_SKATER_STATISTICS:
    FANTASY_SKATER_SCORES.append(request.args.get(i, type = float))
  for i in FANTASY_GOALIE_STATISTICS:
    FANTASY_GOALIE_SCORES.append(request.args.get(i, type = float))

def get_teams():
  print ('The URL response is '+request.full_path.split("?")[1])
  response = requests.get('https://statsapi.web.nhl.com/api/v1/teams/')
  data = response.json()
  return data["teams"]

def returnWord(inputString):
  if len(inputString)==0:
    return ''
  elif (not inputString.islower()):
    return re.sub(r"(?<=\w)([A-Z])", r" \1", inputString).capitalize()
  else:
    return inputString.capitalize()

def returnAcronym(inputString):
  if len(inputString)==0:
    return ''
  else:
    remove_lower = lambda text: re.sub('[a-z]', '', text)
    return (inputString[0]+remove_lower(inputString)).upper()

#playerID is the player's ID, categoryName is the statistical category the user asked for, and perGame is a check on whether or not they want it per game
def createPlotArray(playerID, categoryName, perGame):
  returnList = list()
  print("The categoryName is "+str(categoryName))
  playerCharacteristics = requests.get("https://statsapi.web.nhl.com/api/v1/people/"+str(playerID)).json()
  #The player's current age
  playerAge = playerCharacteristics["people"][0]["currentAge"]
  currentYear = datetime.datetime.now().year
  #Loop to get all the stats for all the years the player has been eligible to play in the league
  while playerAge>=18:
    try:
      playerJSON = requests.get("https://statsapi.web.nhl.com/api/v1/people/"+str(playerID)+"/stats?stats=statsSingleSeason&season="+str(currentYear-1)+str(currentYear)).json()
      playerData = playerJSON['stats'][0]['splits'][0]['stat']
      if categoryName=='age':
          returnList.insert(0,playerAge)
      elif categoryName=='season':
          returnList.insert(0,"'"+str(currentYear)[2:4])
      elif perGame == 'True':
        #Checking if the per game modifier has been checked off
        if 'imeOnIce' in categoryName:
          returnList.insert(0,minuteToDecimal(playerData[categoryName+'PerGame']))
        else:
          returnList.insert(0,playerData[categoryName]/playerData['games'])
      else:
        if 'imeOnIce' in categoryName:
          returnList.insert(0,minuteToDecimal(playerData[categoryName]))
        else:
          returnList.insert(0,playerData[categoryName])
    except IndexError:
      print("No stats for "+str(currentYear-1)+"-"+str(currentYear))
    currentYear-=1
    playerAge-=1
  return returnList

#playerID is the player's ID, weightsArray is the array of weights for each category, and perGame is a check on whether or not they want it per game
def createFantasyGrid(playerID, weightsArray, perGame):
  #This is an array of arrays
  returnList = list()
  playerCharacteristics = requests.get("https://statsapi.web.nhl.com/api/v1/people/"+str(playerID)).json()
  #The player's current age
  playerAge = playerCharacteristics["people"][0]["currentAge"]
  if playerCharacteristics["people"][0]["primaryPosition"]['abbreviation']=='G':
    categoryArray = FANTASY_GOALIE_STATISTICS
  else:
    categoryArray = FANTASY_SKATER_STATISTICS
  returnList = [[] for i in range (len(categoryArray))]
  currentYear = datetime.datetime.now().year
  #Loop to get all the stats for all the years the player has been eligible to play in the league
  while playerAge>=18:
    try:
      playerJSON = requests.get("https://statsapi.web.nhl.com/api/v1/people/"+str(playerID)+"/stats?stats=statsSingleSeason&season="+str(currentYear-1)+str(currentYear)).json()
      playerData = playerJSON['stats'][0]['splits'][0]['stat']
      counter = 0
      #Checking if the per game modifier has been checked off
      if perGame == 'True':
        for i in categoryArray:
          if 'imeOnIce' in i:
            returnList[counter].insert(0,minuteToDecimal(playerData[i+'PerGame'])*weightsArray[counter])
          else:
            returnList[counter].insert(0,playerData[i]/playerData['games']*weightsArray[counter])
          counter+=1
      else:
        for i in categoryArray:
          if 'imeOnIce' in i:
            returnList[counter].insert(0,minuteToDecimal(playerData[i])*weightsArray[counter])
          else:
            returnList[counter].insert(0,playerData[i]*weightsArray[counter])
          counter+=1
    except IndexError:
      print("No stats for "+str(currentYear-1)+"-"+str(currentYear))
    currentYear-=1
    playerAge-=1
  #This returns the points in fantasy the player has gotten in each category, going backwards in year
  return returnList

#This function returns all data for a player in one given season
def get_season_scores(playerID, age, season, getHeader):
  currentSeason = list()
  if getHeader:
    currentSeason.append("Season")
    currentSeason.append("Age")
  else:
    currentSeason.append(str(season-1)+"-"+str(season))
    currentSeason.append(str(age))
  try:
    playerData = requests.get("https://statsapi.web.nhl.com/api/v1/people/"+str(playerID)+"/stats?stats=statsSingleSeason&season="+str(season-1)+str(season)).json()
    playerStats = playerData['stats'][0]['splits'][0]['stat']
    for i in playerStats:
      if (getHeader):
        if (not i.islower()):
           currentSeason.append('<div class="tooltip">'+returnAcronym(i)+'<span class="tooltiptext">'+returnWord(i)+'</span></div>')
        else:
          currentSeason.append(i.capitalize())
      else:
        currentSeason.append(playerStats[i])
  except IndexError:
    currentSeason.append("No stats for "+str(season-1)+"-"+str(season))
  return currentSeason

#This is to generate the options for making the graphs
def getCategories(playerID):
  currentYear = datetime.datetime.now().year
  playerData = requests.get("https://statsapi.web.nhl.com/api/v1/people/"+str(playerID)+"/stats?stats=statsSingleSeason&season="+str(currentYear-1)+str(currentYear)).json()
  playerStats = playerData['stats'][0]['splits'][0]['stat']
  #Top of the string
  topString = '<form action="/generate-chart/" target="_blank" align="center"><div class="row"><div class="column"><h3>Horizontal axis</h3><select id="horizontal" name="horizontal">'
  middleString = '</select></div><div class="column"><h3>Vertical axis</h3><select id="vertical" name="vertical">'
  bottomString = '</select></div></div><br><input type="hidden" class="form-control" name="playerID" id="playerID" value="'+playerID+'"><input type="hidden" class="form-control" name="statsArray" id="statsArray" value="'+str(request.args.get('statsArray', type = str))+'"><input type="checkbox" id="xPerGame" name="xPerGame" value="True"><label for="xPerGame">Generate stats per game in horizontal</label><br><input type="checkbox" id="yPerGame" name="yPerGame" value="True"><label for="yPerGame">Generate stats per game in vertical</label><br><input type="checkbox" id="sameGraph" name="sameGraph" value="True"><label for="sameGraph">Generate output on same graph</label><br><br><input type="submit" value="Generate Chart"></form>'
  selectionOption = '<option value="season">Season</option><option value="age">Age</option>'
  fantasyOption = '<option value="fantasyScore">Fantasy score</option>'
  verticalOption = ''
  for i in playerStats:
    if not "PerGame" in i:
      verticalOption = verticalOption+'<option value="'+i+'">'+returnWord(i)+'</option>'
  return topString+selectionOption+verticalOption+middleString+fantasyOption+verticalOption+bottomString

#player is the part of the JSON that comes from the 'roster' section of the team
def get_player_stats(player, year):
    currentPlayer = list()
    try:
      player_base = "https://statsapi.web.nhl.com/api/v1/people/"+str(player["person"]["id"])+"/stats?stats=statsSingleSeason&season="+year
      playerResponse = requests.get(player_base)
      playerData = playerResponse.json()
      #This variable is the list of all stats for one player
      playerStats = playerData['stats'][0]['splits'][0]['stat']
      
      currentPlayer.append(player["jerseyNumber"])
      currentPlayer.append(player["position"]["abbreviation"])
      #Goalie stats
      if (player["position"]["abbreviation"]=='G'):
        currentPlayer.insert(0,'<a href="'+'/player-page/?fullName='+player["person"]["fullName"]+'&id='+str(player["person"]["id"])+' &statsArray='+str(FANTASY_GOALIE_SCORES)+' "target="_blank">'+player["person"]["fullName"]+'</a>')
        fantasyScore=0
        counter = 0
        #i is the category name, category is the index for the statistic actual value
        for i in FANTASY_GOALIE_STATISTICS:
          fantasyScore += FANTASY_GOALIE_SCORES[counter]*playerStats[i]
          currentPlayer.append(playerStats[i])
          counter+=1
        fantasyScore = round(fantasyScore, 1)
        currentPlayer.insert(3,fantasyScore)
        currentPlayer.insert(4,fantasyScore/playerStats["games"])
        currentPlayer.insert(5,playerStats["games"])
      #Skater stats
      else:
        currentPlayer.insert(0,'<a href="'+'/player-page/?fullName='+player["person"]["fullName"]+'&id='+str(player["person"]["id"])+' &statsArray='+str(FANTASY_SKATER_SCORES)+' "target="_blank">'+player["person"]["fullName"]+'</a>')
        fantasyScore=0
        counter = 0
        #i is the category name, category is the index for the statistic actual value
        for i in FANTASY_SKATER_STATISTICS:
          fantasyScore += FANTASY_SKATER_SCORES[counter]*playerStats[i]
          currentPlayer.append(playerStats[i])
          counter+=1
        currentPlayer.insert(3,fantasyScore)
        currentPlayer.insert(4,fantasyScore/playerStats["games"])
        currentPlayer.insert(5,playerStats["games"])
        currentPlayer.insert(8,playerStats["points"])
    #This only happens for players who are on the roster, but haven't played any games
    except IndexError:
      print("No stats for "+currentPlayer[0])
    return currentPlayer

def check_viability(position):
  #These are the positions that the users selected (LW, RW, C, D, G, F, S)
  #Position is the current player
  allowedPositions = request.args.get('positions', type = str)
  if (allowedPositions=="left"):
    return (position=='LW')
  elif (allowedPositions=='right'):
    return (position=='RW')
  elif (allowedPositions=='center'):
    return (position=='C')
  elif (allowedPositions=='defense'):
    return (position=='D')
  elif (allowedPositions=='goalie'):
    return (position=='G')
  elif (allowedPositions=='all'):
    return True
  elif (allowedPositions=='skater'):
    return (position!='G')
  elif (allowedPositions=='forward'):
    return (position!='G' and position!='D')

#This function returns a list of all players on each team
def get_all_players():
  teams = get_teams()
  all_players = list()
  currentYear = datetime.datetime.now().year
  enterYear = str(currentYear-1)+str(currentYear)
  #x is an array of teams and their stats
  for x in teams:
    api_url_base = 'https://statsapi.web.nhl.com/api/v1/teams/' + str(x["id"]) + '/roster'
    teamResponse = requests.get(api_url_base)
    teamData = teamResponse.json()
    print("Writing "+x["name"])
    #i is an array of players and their stats
    for i in teamData["roster"]:
      try:
        if check_viability(i["position"]["abbreviation"]):
          currentPlayer = get_player_stats(i, enterYear)
          all_players.append(currentPlayer)
      except IndexError:
        print("No stats for "+i["person"]["fullName"])
  print ("Begin sorting...")
  if request.args.get('sort', type = str)=="total":
    all_players.sort(reverse=True, key=lambda x: float(x[3]))
  elif request.args.get('sort', type = str)=="game":
    all_players.sort(reverse=True, key=lambda x: float(x[4]))
  return all_players

#This function gets called first, and calls the other functions
def return_players_last_season():
  print("Begin printing...")
  allPlayers = get_all_players()
  counter = 0
  print("Begin printing HTML file")
  #We manually append everything because I tried doing it via queue, and it took up a whole week to implement, and it made it 10x slower anyways
  headerString = "<tr><th>Rank</th><th>Name</th><th>Number</th><th>Position</th><th>Fantasy Score</th><th>Fantasy Score Per Game</th><th>GP</th>"
  returnString = "<style>"+getTableProperties()+"</style>"
  returnString = returnString + '<table align="center" style="float:center"><h1 style="text-align:center;">Most fantasy points last season in '+request.args.get('sort', type = str)+', '+request.args.get('positions', type = str)+'</h2>'
  if request.args.get('positions', type = str)=="goalie":
    headerString = headerString + "<th>Wins</th><th>Goals Against</th><th>Saves</th><th>Shutouts</th></tr>"
  elif request.args.get('positions', type = str)=="all":
    headerString = headerString + "<th>Goals(Wins)</th><th>Assists(GA)</th><th>Points(SV)</th><th>PIM(SO)</th><th>PPP</th><th>SHP</th><th>SOG</th><th>HIT</th><th>BLK</th></tr>"
  else:
    headerString = headerString + "<th>Goals</th><th>Assists</th><th>Points</th><th>PIM</th><th>PPP</th><th>SHP</th><th>SOG</th><th>HIT</th><th>BLK</th></tr>"
  returnString = returnString + headerString
  #This goes through the entire list of players
  #i is an array of a player and their stats
  for i in allPlayers:
    counter+=1
    if counter%20==0:
      returnString = returnString + headerString
    try:
      returnString = returnString +'<td>'+ str(counter) +'</td>'
      for j in i:
          returnString = returnString +'<td>'+ str(j) +'</td>'
      returnString = returnString + '</tr>'
    #This only happens for players who are on the roster, but haven't played any games
    except IndexError:
      print("No stats for "+i[0])
  returnString = returnString+"</table>"
  print(str(counter)+" players counted.")
  return returnString

def return_player_data(playerID):
  currentYear = datetime.datetime.now().year
  returnString = ''
  playerCharacteristics = requests.get("https://statsapi.web.nhl.com/api/v1/people/"+str(playerID)).json()
  #The player's current age
  playerAge = playerCharacteristics["people"][0]["currentAge"]
  currentSeasonStats = get_season_scores(playerID, playerAge, currentYear, True)
  for j in currentSeasonStats:
      returnString = returnString +'<th>'+ str(j) +'</th>'
  currentSeasonStats = get_season_scores(playerID, playerAge, currentYear, False)
  while playerAge>=18:
    print ("Generating stats for "+str(currentYear))
    returnString = returnString + '<tr>'
    for j in currentSeasonStats:
      returnString = returnString +'<td>'+ str(j) +'</td>'
    returnString = returnString + '</tr>'
    currentYear-=1
    playerAge-=1
    currentSeasonStats = get_season_scores(playerID, playerAge, currentYear, False)
  return returnString

def minuteToDecimal(timeString):
  stringSplit = timeString.split(':')
  return int(stringSplit[0])+(int(stringSplit[1])/60)

@app.route('/generate-chart/')
def makePlot():
  playerID = str(request.args.get('playerID', type = str))
  startTime = time.perf_counter()
  playerCharacteristics = requests.get("https://statsapi.web.nhl.com/api/v1/people/"+str(playerID)).json()
  #These are the values as recieved
  horizontalInput = str(request.args.get('horizontal', type = str))
  verticalInput = str(request.args.get('vertical', type = str))
  print("The vertical Input is "+verticalInput)
  horizontalAxis = createPlotArray(playerID, horizontalInput, request.args.get('xPerGame', type = str))
  verticalAxis = list()
  fantasyGrid = list()
  categoryArray = list()
  #Special section for fantasy scores
  if (verticalInput)=='fantasyScore':
    #statisticsArray is the name of the category, valueArray contains the values associated with each category
    valuesArray = eval(request.args.get('statsArray', type = str))
    fantasyGrid = createFantasyGrid(playerID, valuesArray, request.args.get('yPerGame', type = str))
    score = 0
    counter = 0
    playerAge = playerCharacteristics["people"][0]["currentAge"]
    while playerAge>=18:
      try:
        #This is an array of arrays
        for i in fantasyGrid:
          score = score+i[counter]
        verticalAxis.append(score)
        score = 0
      except IndexError:
        print("No stats for age "+str(playerAge))
      playerAge-=1
      counter+=1
  else:
    verticalAxis = createPlotArray(playerID, verticalInput, request.args.get('yPerGame', type = str))
  #Give the axes proper names
  horizontalTitle = ''
  verticalTitle = ''
  horizontalTitle = returnWord(horizontalInput)
  verticalTitle = returnWord(verticalInput)
  if playerCharacteristics["people"][0]["primaryPosition"]['abbreviation']=='G':
    categoryArray = FANTASY_GOALIE_STATISTICS
  else:
    categoryArray = FANTASY_SKATER_STATISTICS
  if "imeOnIce" in horizontalInput:
    horizontalTitle = horizontalTitle + " in minutes"
  if "imeOnIce" in verticalInput:
    verticalTitle = verticalTitle + " in minutes"
  counter = 0
  #Make the plots
  fig, ax = plt.subplots()
  if (str(request.args.get('horizontal', type = str))=='age' or str(request.args.get('horizontal', type = str))=='season'):
    if str(request.args.get('sameGraph', type = str))=='True' and verticalInput=='fantasyScore':
      #i is the name of the category
      for i in categoryArray:
        ax.plot(horizontalAxis, fantasyGrid[counter], linestyle='--', marker='o', label = returnWord(i))
        counter+=1
      ax.plot(horizontalAxis, verticalAxis, linestyle='--', marker='o', color='r', label = 'Fantasy score')
    else:
      ax.plot(horizontalAxis, verticalAxis, linestyle='--', marker='o', color='r', label = 'Data')
  else:
    ax.scatter(horizontalAxis, verticalAxis, c='#000000', s = 10, label = "Data", alpha=0.5, marker="+")
  #Labels for the axes
  if (str(request.args.get('xPerGame', type = str) == 'True' and not(horizontalInput=='age' or horizontalInput=='season'))=='True'):
    horizontalTitle = horizontalTitle + " per game"
  if str(request.args.get('yPerGame', type = str)) == 'True':
    verticalTitle = verticalTitle + " per game"
  ax.set_xlabel(horizontalTitle)
  ax.set_ylabel(verticalTitle)
  ax.set_title(playerCharacteristics["people"][0]["fullName"])  # Add a title to the graph.
  ax.legend(loc='upper left')  # Add a legend.
  if os.path.isfile('plots/currentChart.png') and str(request.args.get('sameGraph', type = str))!='True':
    print("Deleting previously found graph")
    os.remove('plots/currentChart.png') 
  plt.savefig('plots/currentChart.png')
  #full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'currentChart.png')
  #print ("the filename is "+full_filename)
  #print ("The pwd is "+os.getcwd())
  endTime = time.perf_counter()
  print("Chart generated in "+str(endTime-startTime)+" seconds.")
  im = Image.open(r"plots/currentChart.png")
  im.show()
  #return render_template("plotPage.html", user_image = full_filename)
  return '<h3>Image Generated</h3>'

#This function is to get the results for when you hover over an abbreviated category
def getToolTip():
  f = open("templates/tooltipStyle.html", "r")
  style = f.read()
  f.close()
  return style

def getTableProperties():
  f = open("templates/tableStyles.html", "r")
  style = f.read()
  f.close()
  return style

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/player-page/')
def player_link():
  startTime = time.perf_counter()
  print ("Fetching player data for "+request.args.get('fullName', type = str))
  playerID = request.args.get('id', type = str)
  #Current issue: the value for str(request.args.get('statsArray', type = str)) doesn't pass over to the getCategories function
  playerString = "<style>"+getTableProperties()+getToolTip()+"</style><table align='center style='float:center'><h1 style='text-align:center;' >"+'<a href="https://www.nhl.com/player/'+str(playerID)+'"target="_blank">'+request.args.get('fullName', type = str)+'</a>'+"</h1><br><br><br><tr>"+return_player_data(playerID)+"</table>"+getCategories(playerID)
  endTime = time.perf_counter()
  print("Player's stats fetched in "+str(endTime-startTime)+" seconds.")
  return playerString

@app.route('/my-link/')
def my_link():
  startTime = time.perf_counter()
  getFantasyStatistics()
  #return return_teams()
  fileNameString = "saves/"+str(datetime.datetime.now().year)+request.full_path.split("?")[1]
  seasonString =""
  #Load the saved file if it exists, to save time
  if os.path.isfile(fileNameString):
    print ("Saved file found")
    f = open(fileNameString, "r")
    seasonString = f.read()
    f.close()
  else: 
    print("No saved file found. Generating.")
    seasonString = return_players_last_season()
    f = open(fileNameString, "w+")
    f.write(seasonString)
    f.close() 
  endTime = time.perf_counter()
  print("League rankings ran in "+str(endTime-startTime)+" seconds.")
  return seasonString


if __name__ == '__main__':
  app.run(debug=True)
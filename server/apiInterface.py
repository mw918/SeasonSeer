import json
import requests
import datetime
import time
import os.path
import re
from flask import Flask, render_template, request
app = Flask(__name__)

def get_teams():
  print ('The URL response is '+request.full_path.split("?")[1])
  response = requests.get('https://statsapi.web.nhl.com/api/v1/teams/')
  data = response.json()
  return data["teams"]

#This function returns all data for a player in one given season
def get_season_scores(playerID, season, getHeader):
  currentSeason = list()
  remove_lower = lambda text: re.sub('[a-z]', '', text)
  if getHeader:
    currentSeason.append("Season")
  else:
    currentSeason.append(str(season-1)+"-"+str(season))
  try:
    playerData = requests.get("https://statsapi.web.nhl.com/api/v1/people/"+str(playerID)+"/stats?stats=statsSingleSeason&season="+str(season-1)+str(season)).json()
    playerStats = playerData['stats'][0]['splits'][0]['stat']
    for i in playerStats:
      if (getHeader):
        if (not i.islower()):
          #currentSeason.append((i[0]+remove_lower(i)).upper())
           currentSeason.append('<div class="tooltip">'+(i[0]+remove_lower(i)).upper()+'<span class="tooltiptext">'+re.sub(r"(?<=\w)([A-Z])", r" \1", i).capitalize()+'</span></div>')
        else:
          currentSeason.append(i)
      else:
        currentSeason.append(playerStats[i])
  except IndexError:
    currentSeason.append("No stats for "+str(season-1)+"-"+str(season))
  return currentSeason

#player is the part of the JSON that comes from the 'roster' section of the team
def get_player_stats(player):
    currentPlayer = list()
    try:
      currentYear = datetime.datetime.now().year
      player_base = "https://statsapi.web.nhl.com/api/v1/people/"+str(player["person"]["id"])+"/stats?stats=statsSingleSeason&season="+str(currentYear-1)+str(currentYear)
      playerResponse = requests.get(player_base)
      playerData = playerResponse.json()
      #This variable is the list of all stats for one player
      playerStats = playerData['stats'][0]['splits'][0]['stat']
      #currentPlayer.append('<a href="https://www.nhl.com/player/'+str(player["person"]["id"])+'"target="_blank">'+player["person"]["fullName"]+'</a>')
      currentPlayer.append('<a href="'+'/player-page/?fullName='+player["person"]["fullName"]+'&id='+str(player["person"]["id"])+' "target="_blank">'+player["person"]["fullName"]+'</a>')
      currentPlayer.append(player["jerseyNumber"])
      currentPlayer.append(player["position"]["abbreviation"])
      #Goalie stats
      if (player["position"]["abbreviation"]=='G'):
        win = request.args.get('win', type = float) * playerStats["wins"]
        ga = request.args.get('ga', type = float) * playerStats["goalsAgainst"]
        save = request.args.get('save', type = float) * playerStats["saves"]
        shutout = request.args.get('so', type = float) * playerStats["shutouts"]
        fantasyScore = round(win + ga + save + shutout, 1)
        pointsPerGame = fantasyScore/playerStats["games"]
        currentPlayer.append(str(fantasyScore))
        currentPlayer.append(str(pointsPerGame))
        currentPlayer.append(str(playerStats["games"]))
        currentPlayer.append(str(playerStats["wins"]))
        currentPlayer.append(str(playerStats["goalsAgainst"]))
        currentPlayer.append(str(playerStats["saves"]))
        currentPlayer.append(str(playerStats["shutouts"]))
      #Skater stats
      else:
        goals = request.args.get('goals', type = float) * playerStats["goals"]
        assists = request.args.get('assists', type = float) * playerStats["assists"]
        pim = request.args.get('pim', type = float) * playerStats["pim"]
        ppp = request.args.get('ppp', type = float) * playerStats["powerPlayPoints"]
        shp = request.args.get('shp', type = float) * playerStats["shortHandedPoints"]
        sog = request.args.get('sog', type = float) * playerStats["shots"]
        hit = request.args.get('hit', type = float) * playerStats["hits"]
        blk = request.args.get('blk', type = float) * playerStats["blocked"]
        fantasyScore = goals + assists + pim + ppp + shp + sog + hit + blk
        pointsPerGame = fantasyScore/playerStats["games"]
        currentPlayer.append(str(fantasyScore))
        currentPlayer.append(str(pointsPerGame))
        currentPlayer.append(str(playerStats["games"]))
        currentPlayer.append(str(playerStats["goals"]))
        currentPlayer.append(str(playerStats["assists"]))
        currentPlayer.append(str(playerStats["points"]))
        currentPlayer.append(str(playerStats["pim"]))
        currentPlayer.append(str(playerStats["powerPlayPoints"]))
        currentPlayer.append(str(playerStats["shortHandedPoints"]))
        currentPlayer.append(str(playerStats["shots"]))
        currentPlayer.append(str(playerStats["hits"]))
        currentPlayer.append(str(playerStats["blocked"]))
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
          currentPlayer = get_player_stats(i)
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
  #We manually append everything because I tried doing it via queue, and it took up a whole week to implement, and it made it 10x slower anyways
  headerString = "<tr><th>Rank</th><th>Name</th><th>Number</th><th>Position</th><th>Fantasy Score</th><th>Fantasy Score Per Game</th><th>GP</th>"
  returnString = "<style>"+getTableProperties()+"</style>"
  returnString = returnString + '<table style="float:center"><h1>Most fantasy points last season in '+request.args.get('sort', type = str)+', '+request.args.get('positions', type = str)+'</h2>'
  if request.args.get('positions', type = str)=="goalie":
    headerString = headerString + "<th>Wins</th><th>Goals Against</th><th>Saves</th><th>Shutouts</th></tr>"
  elif request.args.get('positions', type = str)=="all":
    headerString = headerString + "<th>Goals(Wins)</th><th>Assists(GA)</th><th>Points(SV)</th><th>PIM(SO)</th><th>PPP</th><th>SHP</th><th>SOG</th><th>HIT</th><th>BLK</th></tr>"
  else:
    headerString = headerString + "<th>Goals</th><th>Assists</th><th>Points</th><th>PIM</th><th>PPP</th><th>SHP</th><th>SOG</th><th>HIT</th><th>BLK</th></tr>"
  #<th>GP</th><th>Goals</th><th>Assists</th><th>Points</th><th>PIM</th><th>PPP</th><th>SHP</th><th>SOG</th><th>HIT</th><th>BLK</th></tr>
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
          returnString = returnString +'<td>'+ j +'</td>'
      '''
      #Goalie stats
      if (i[2]=='G'):
        if request.args.get('positions', type = str)=="goalie":
          for j in i:
            returnString = returnString +'<td>'+ j +'</td>'
        else:
          for j in range(6):
            returnString = returnString + '<td>'+ i[j] + '</td>'
        #Skater stats
      else:
        for j in i:
          returnString = returnString +'<td>'+ j +'</td>'
          '''
      returnString = returnString + '</tr>'
    #This only happens for players who are on the roster, but haven't played any games
    except IndexError:
      print("No stats for "+i[0])
  returnString = returnString+"</table>"
  print(str(counter)+" players counted.")
  return returnString

'''
#This block of code is basically obsolete
def return_teams():
    startTime = time.perf_counter()
    teams = get_teams()
    rosterString = "<style>table, th, td {border: 2px solid powderblue;}</style>"
    goalieString = "<table style='float:center'><caption>Goalie Stats</caption>"
    goalieString = goalieString + "<tr><th>Name</th><th>Number</th><th>Position</th><th>Team</th><th>Fantasy Score</th><th>Wins</th><th>GA</th><th>SV</th><th>SO</th></tr>"
    #This loop goes through the teams one by one
    for x in teams:
        api_url_base = 'https://statsapi.web.nhl.com/api/v1/teams/' + str(x["id"]) + '/roster'
        teamResponse = requests.get(api_url_base)
        teamData = teamResponse.json()
        currentTeam = ""
        currentGoalies = ""
        print("Writing "+x["name"])
        currentTeam = currentTeam + '<table style="float:center"><caption><a href="'+x["officialSiteUrl"]+'" target="_blank">'+x["name"]+'</a></caption>'
        currentTeam = currentTeam + "<tr><th>Name</th><th>Number</th><th>Position</th><th>Fantasy Score</th><th>GP</th><th>Goals</th><th>Assists</th><th>Points</th><th>PIM</th><th>PPP</th><th>SHP</th><th>SOG</th><th>HIT</th><th>BLK</th></tr>"
        #This loop goes through the members of the roster one by one
        for i in teamData["roster"]:
          try:
            currentPlayer = get_player_stats(i)
            playerSpecs = '<tr><td><a href="https://www.nhl.com/player/'+str(i["person"]["id"])+'"target="_blank">'+currentPlayer[0]+'</a></td>'
            list_iter = iter(currentPlayer)
            next(list_iter)
            currentTeam = currentTeam + playerSpecs
            for j in list_iter:
                currentTeam = currentTeam +'<td>'+ j +'</td>'
            #Goalie stats
            if (i["position"]["abbreviation"]=='G'):
              currentTeam = currentTeam + '<td>'+currentPlayer[1] + '</td><td>'+ currentPlayer[2] + '</td><td>'+ currentPlayer[3] + '</td></tr>'
              for j in list_iter:
                currentGoalies = currentGoalies +'<td>'+j +'</td>'
              #Skater stats
            else:
              for j in list_iter:
                currentTeam = currentTeam +'<td>'+ j +'</td>'
            currentTeam = currentTeam + '</tr>'
          #This only happens for players who are on the roster, but haven't played any games
          except IndexError:
            print("No stats for "+i["person"]["fullName"])
        currentTeam = currentTeam + "</table>"
        currentTeam = currentTeam + "<br>"
        rosterString = rosterString+currentTeam
        goalieString = goalieString+currentGoalies
    print("Writing goalie stats")
    rosterString = rosterString+goalieString+"</table>"
    endTime = time.perf_counter()
    print("App ran in "+str(endTime-startTime)+" seconds.")
    return rosterString
'''

def return_player_data(playerID):
  currentYear = datetime.datetime.now().year
  returnString = ''
  currentSeasonStats = get_season_scores(playerID, currentYear, True)
  for j in currentSeasonStats:
      returnString = returnString +'<th>'+ str(j) +'</th>'
  currentSeasonStats = get_season_scores(playerID, currentYear, False)
  while currentSeasonStats[1] != "No stats for "+str(currentYear-1)+"-"+str(currentYear):
    #print ("Getting data for "+str(currentYear-1)+"-"+str(currentYear))
    #print ("The value for currentSeasonStats[1] is "+currentSeasonStats[1])
    print ("Generating stats for "+str(currentYear))
    returnString = returnString + '<tr>'
    for j in currentSeasonStats:
      returnString = returnString +'<td>'+ str(j) +'</td>'
    returnString = returnString + '</tr>'
    currentYear-=1
    currentSeasonStats = get_season_scores(playerID, currentYear, False)
  return returnString

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
  playerString = "<style>table, td, th {border: 2px solid powderblue}"+getToolTip()+"</style><table style='float:center'><h1>"+'<a href="https://www.nhl.com/player/'+str(request.args.get('id', type = str))+'"target="_blank">'+request.args.get('fullName', type = str)+'</a>'+"</h1><br><br><br><tr>"+return_player_data(request.args.get('id', type = str))+"</table>"
  endTime = time.perf_counter()
  print("App ran in "+str(endTime-startTime)+" seconds.")
  return playerString

@app.route('/my-link/')
def my_link():
  startTime = time.perf_counter()
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
  print("App ran in "+str(endTime-startTime)+" seconds.")
  return seasonString


if __name__ == '__main__':
  app.run(debug=True)
import json
import requests
import datetime
import time
from flask import Flask, render_template, request
app = Flask(__name__)

def get_teams():
  print ('I got clicked!')
  response = requests.get('https://statsapi.web.nhl.com/api/v1/teams/')
  data = response.json()
  return data["teams"]

def get_categories():
  #The list of every category that can be turned on or off
  categories = list()
  
  categories.append("showCharjerseyNumber")
  categories.append("showCharposition")
  categories.append("showCharcurrentTeam")

  categories.append("InTotal")
  categories.append("PerGame")

  if request.args.get('positions', type = str)=="goalie":
    categories.append("showGoaliegames")
    categories.append("showGoaliewins")
    categories.append("showGoaliegoalsAgainst")
    categories.append("showGoaliesaves")
    categories.append("showGoalieshutouts")
  else:
    categories.append("showgames")
    categories.append("showgoals")
    categories.append("showassists")
    categories.append("showpoints")
    categories.append("showpim")
    categories.append("showpowerPlayPoints")
    categories.append("showshortHandedPoints")
    categories.append("showshots")
    categories.append("showhits")
    categories.append("showblocked")

  for i in categories:
    #The category has been selected to be displayed by the user
    if str(request.args.get(i, type = str)) == "None":
      del(i)

  return (categories)

#player is the part of the JSON that comes from the 'roster' section of the team
def get_player_stats(player, team):
    currentPlayer = list()
    try:
      currentYear = datetime.datetime.now().year
      player_base = "https://statsapi.web.nhl.com/api/v1/people/"+str(player["person"]["id"])+"/stats?stats=statsSingleSeason&season="+str(currentYear-1)+str(currentYear)
      playerResponse = requests.get(player_base)
      playerData = playerResponse.json()
      fantasyScore=0
      pointsPerGame=0
      #This variable is the list of all stats for one player
      playerStats = playerData['stats'][0]['splits'][0]['stat']
      currentPlayer.append('<a href="https://www.nhl.com/player/'+str(player["person"]["id"])+'"target="_blank">'+player["person"]["fullName"]+'</a>')

      #Goalie stats
      if (player["position"]["abbreviation"]=='G'):
        win = request.args.get('win', type = float) * playerStats["wins"]
        ga = request.args.get('ga', type = float) * playerStats["goalsAgainst"]
        save = request.args.get('save', type = float) * playerStats["saves"]
        shutout = request.args.get('so', type = float) * playerStats["shutouts"]
        fantasyScore = round(win + ga + save + shutout, 1)
        pointsPerGame = fantasyScore/playerStats["games"]
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
      #i is the name as it appears in the JSON, the requested value is the one that'll appear in the column heading
      for i in global_categories:
        #The category has been selected to be displayed by the user
        if str(request.args.get(i, type = str)) != "None":
          #Player characteristics
          if i[4:8]=="Char":
            #Need to check for team name, since it has an additional level
            if (i[8:len(i)]=="currentTeam"):
              currentPlayer.append(team)
            elif (i[8:len(i)]=="position"):
              currentPlayer.append(str(player["position"]["abbreviation"]))
            else:
              currentPlayer.append(str(player[str(i)[8:len(i)]]))
          #Stats from API (goals, assists, etc.)
          elif i[0:4]=="show":
            #Goalie stats only shown if goalies-only is selected
            if request.args.get('positions', type = str)=="goalie":
              if i[4:10]=="Goalie":
                currentPlayer.append(str(playerStats[str(i)[10:len(i)]]))
            #If something other than goalies are selected
            else:
              if i[4:10]!="Goalie" and player["position"]["abbreviation"]!="G":
                currentPlayer.append(str(playerStats[str(i)[4:len(i)]]))
          #Calculated categories
          else:
            if i=="InTotal":
              currentPlayer.append(str(fantasyScore))
            elif i=="PerGame":
              currentPlayer.append(str(pointsPerGame))
            else:
              print("Unrecognized category "+i)
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

def get_all_players():
  teams = get_teams()
  all_players = list()
  #x is an array of teams and their stats
  for x in teams:
    api_url_base = 'https://statsapi.web.nhl.com/api/v1/teams/' + str(x["id"]) + '/roster'
    teamResponse = requests.get(api_url_base)
    teamData = teamResponse.json()
    print("Writing"+x["name"])
    #i is an array of players and their stats
    for i in teamData["roster"]:
      try:
        if check_viability(i["position"]["abbreviation"]):
          currentPlayer = get_player_stats(i, x["name"])
          all_players.append(currentPlayer)
      except IndexError:
        print("No stats for "+i["person"]["fullName"])
  print ("Begin sorting...")
  #Get the basis from which I'm sorting
  value = request.args.get('sort', type = str)
  indexOfValue = global_categories.index(value[4:len(value)])
  all_players.sort(reverse=True, key=lambda x: float(x[indexOfValue]))
  '''if request.args.get('sort', type = str)=="total":
    all_players.sort(reverse=True, key=lambda x: float(x[3]))
  elif request.args.get('sort', type = str)=="game":
    all_players.sort(reverse=True, key=lambda x: float(x[4]))'''
  return all_players

def return_players_last_season():
  startTime = time.perf_counter()
  counter = 0
  print("Begin printing...")
  allPlayers = get_all_players()
  returnString = "<style>table, th, td {border: 2px solid powderblue;}</style>"
  returnString = returnString + '<table style="float:center"><h1>Most fantasy points last season by '+request.args.get('positions', type = str)+'</h2>'
  headerString = "<tr><th>Rank</th><th>Name</th>"
  #This is to print out all the categories along the top
  for i in global_categories:
    #The category has been selected to be displayed by the user
    if str(request.args.get(i, type = str)) != "None":
      #Print out all categories relevant to goalies
      if request.args.get('positions', type = str)=="goalie":
        if str(i)[4:10]=="Goalie" or str(i)[4:8]=="Char" or str(i)[0:4]!="show":
          headerString = headerString+"<th>"+str(request.args.get(i, type = str))+"</th>"
      #Print out all categories relevant to skaters
      else:
        if str(i)[4:10]!="Goalie":
          headerString = headerString+"<th>"+str(request.args.get(i, type = str))+"</th>"
  headerString = headerString+"</tr>"
  returnString = returnString + headerString
  #This goes through the entire list of players
  #i is an array of a player and their stats
  for i in allPlayers:
    counter+=1
    if counter%20==0:
      returnString = returnString + headerString
    try:
      returnString = returnString +'<td>'+ str(counter) +'</td>'
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
      returnString = returnString + '</tr>'
    #This only happens for players who are on the roster, but haven't played any games
    except IndexError:
      print("No stats for "+i[0])
  returnString = returnString+"</table>"
  endTime = time.perf_counter()
  print("App ran in "+str(endTime-startTime)+" seconds. "+str(counter)+" players counted.")
  return returnString

#This section is more or less obsolete
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
            currentPlayer = get_player_stats(i, x["name"])
            playerSpecs = '<tr><td><a href="https://www.nhl.com/player/'+str(i["person"]["id"])+'"target="_blank">'+currentPlayer[0]+'</a></td>'
            list_iter = iter(currentPlayer)
            next(list_iter)
            currentTeam = currentTeam + playerSpecs
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

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/calculate-results/')
def my_link():
  #return return_teams()
  global global_categories
  global_categories = get_categories()
  return return_players_last_season()


if __name__ == '__main__':
  app.run(debug=True)
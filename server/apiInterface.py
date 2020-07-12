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

#def get_player_stats():


def return_teams():
    startTime = time.perf_counter()
    teams = get_teams()
    skaterStats = list()
    goalieStats = list()
    rosterString = "<style>table, th, td {border: 2px solid powderblue;}</style>"
    goalieString = "<table style='float:center'><caption>Goalie Stats</caption>"
    goalieString = goalieString + "<tr><th>Name</th><th>Number</th><th>Position</th><th>Team</th><th>Fantasy Score</th><th>Wins</th><th>GA</th><th>SV</th><th>SO</th></tr>"
    currentYear = datetime.datetime.now().year
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
            player_base = "https://statsapi.web.nhl.com/api/v1/people/"+str(i["person"]["id"])+"/stats?stats=statsSingleSeason&season="+str(currentYear-1)+str(currentYear)
            playerResponse = requests.get(player_base)
            playerData = playerResponse.json()
            #This variable is the list of all stats for one player
            currentPlayer = list()
            playerStats = playerData['stats'][0]['splits'][0]['stat']
            playerSpecs = '<tr><td><a href="https://www.nhl.com/player/'+str(i["person"]["id"])+'"target="_blank">'+i["person"]["fullName"]+'</a></td><td>'+i["jerseyNumber"]+'</td><td>'+i["position"]["abbreviation"]+'</td>'
            currentTeam = currentTeam + playerSpecs
            #Goalie stats
            if (i["position"]["abbreviation"]=='G'):
              win = request.args.get('win', type = float) * playerStats["wins"]
              ga = request.args.get('ga', type = float) * playerStats["goalsAgainst"]
              save = request.args.get('save', type = float) * playerStats["saves"]
              shutout = request.args.get('so', type = float) * playerStats["shutouts"]
              fantasyScore = round(win + ga + save + shutout, 1)
              currentTeam = currentTeam + '<td>' + str(fantasyScore) + '</td></tr>'
              currentGoalies = currentGoalies+'<tr>'+playerSpecs + '</td><td><a href="'+x["officialSiteUrl"]+'" target="_blank">'+x["name"]+'</a></td><td>'+ str(fantasyScore)+'</td><td>'+ str(playerStats["wins"])+'</td><td>'+ str(playerStats["goalsAgainst"])+'</td><td>'+ str(playerStats["saves"])+'</td><td>'+ str(playerStats["shutouts"])+'</tr>'
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
              currentTeam = currentTeam + '<td>' + str(fantasyScore)+'</td><td>'+ str(playerStats["games"])+'</td><td>'+str(playerStats["goals"])+'</td><td>'+str(playerStats["assists"])+'</td><td>'+str(playerStats["points"])+'</td><td>'+str(playerStats["pim"])+'</td><td>'+str(playerStats["powerPlayPoints"])+'</td><td>'+str(playerStats["shortHandedPoints"])+'</td><td>'+str(playerStats["shots"])+'</td><td>'+str(playerStats["hits"])+'</td><td>'+str(playerStats["blocked"])+'</td></tr>'
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
    print("App ran in "+str(endTime-startTime)+" seconds")
    return rosterString

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/my-link/')
def my_link():
  return return_teams()


if __name__ == '__main__':
  app.run(debug=True)
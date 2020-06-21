import json
import requests

def get_teams():
    response = requests.get('https://statsapi.web.nhl.com/api/v1/teams/')
    data = response.json()
    return data["teams"]

def write_roster():
    teams = get_teams()
    f = open("rosters.txt", "w")
    for x in teams:
        api_url_base = 'https://statsapi.web.nhl.com/api/v1/teams/' + str(x["id"]) + '/roster'
        response = requests.get(api_url_base)
        data = response.json()
        print("Writing "+x["name"])
        f.write("\n\n" + x["name"] + ":")
        for i in data["roster"]:
            f.write("\n"+i["person"]["fullName"]+" "+ i["jerseyNumber"]+" "+ i["position"]["abbreviation"])
    f.close()
    print("Done writing")

write_roster()
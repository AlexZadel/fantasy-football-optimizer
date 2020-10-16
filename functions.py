#import libraries
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# PART 1 FUNCTIONS

# web scraping function
def scrape_to_soup(url):
    print("Scraping...", url)
    text = requests.get(url)
    soup = BeautifulSoup(text.text, 'lxml')
    return soup


# fn to extract url slug from main page, convert to player stats page url
def player_slug(row):
    regex = r"[^/]+.(?:php)"  #regular expression to extract just the first-last name section of url
    base = 'https://www.fantasypros.com/nfl/games/'   #base part of url for player stats page

    start_url = row.findAll('td')[1].findAll('a')[0]['href']  #extract player url
    match = re.findall(regex, start_url)  #get just the ending part (player name with .php)
    new_url = base + match[0]   #concat to get new url for game log piece
    return new_url


# fn to build a player dictionary
def build_a_player(row):
    player = {}
    cells = row.findAll('td')
    player['name'] = cells[1].text
    player['url'] = player_slug(row)
    player['team'] = cells[2].text
    player['pos'] = cells[3].text

    return player




# PART 4 FUNCTIONS

# function to calculate the projected score of a player (non defenses)
def proj_player_score(players):
    players['proj_score'] = 0
    n_players = players.shape[0]

    for player in range(n_players):       #iterate through players
        # aliases for stats
        yds_passing = players.loc[player, 'yds_passing']
        tds_passing = players.loc[player, 'tds_passing']
        yds_receiving = players.loc[player, 'yds_receiving']
        tds_receiving = players.loc[player, 'tds_receiving']
        yds_rushing = players.loc[player, 'yds_rushing']
        tds_rushing = players.loc[player, 'tds_rushing']
        conversion_rushing = players.loc[player, 'conversion_rushing']
        conversion_received = players.loc[player, 'conversion_received']
        conversion_pass = players.loc[player, 'conversion_pass']
        interceptions = players.loc[player, 'interceptions']
        fumbles = players.loc[player, 'fumbles']
        team = players.loc[player, 'team']

        #calculate score
        players.loc[player, 'proj_score'] = .04*yds_passing + 4*tds_passing + 2*conversion_pass + (-2)*interceptions + .1*yds_rushing + 6*tds_rushing + 2*conversion_rushing + .1*yds_receiving + 6*tds_receiving + 2*conversion_received + (-2)*fumbles

    return players



#fn to calculate the score of a defense/special teams player

def proj_defense_score(defenses):
    defenses['proj_score'] = 0
    n_ds = defenses.shape[0]

    for defense in range(n_ds):
        turnover_tds = defenses.loc[defense, 'turnover_tds']
        turnovers  = defenses.loc[defense, 'turnovers']
        safety =  defenses.loc[defense, 'safety']
        sacks = defenses.loc[defense, 'sacks']
        pts_against = defenses.loc[defense, 'pts_against']

        #calculate pts score based on pts against
        if pts_against == 0:
            pts_score = 10
        elif (pts_against > 0 & pts_against < 7):
            pts_score = 7
        elif (pts_against > 6 & pts_against < 14):
            pts_score = 4
        elif (pts_against > 13 & pts_against < 21):
            pts_score = 1
        elif (pts_against > 20 & pts_against < 28):
            pts_score = 0
        elif (pts_against > 27 & pts_against < 35):
            pts_score = -1
        elif (pts_against > 34):
            pts_score = -4

        defenses.loc[defense, 'proj_score'] =  sacks + 2*turnovers + 2*safety + 6*turnover_tds + pts_score

    return defenses




#fn to build team complete with scoring and cost information
def compile_team(qb, rb1, rb2, wr1, wr2, wr3, te, flex, defense, df1=players, df2=defenses):

    #initialize
    team_list = [qb, rb1, rb2, wr1, wr2, wr3, te, flex]
    new_team = {}
    cost = 0
    proj_score = 0

    #
    new_team['qb'] = str((qb, df1.loc[qb, 'cost'], int(df1.loc[qb, 'proj_score'])))
    new_team['rb1'] = str((rb1, df1.loc[rb1, 'cost'], int(df1.loc[rb1, 'proj_score'])))
    new_team['rb2'] = str((rb2, df1.loc[rb2, 'cost'], int(df1.loc[rb2, 'proj_score'])))
    new_team['wr1'] = str((wr1, df1.loc[wr1, 'cost'], int(df1.loc[wr1, 'proj_score'])))
    new_team['wr2'] = str((wr2, df1.loc[wr2, 'cost'], int(df1.loc[wr2, 'proj_score'])))
    new_team['wr3'] = str((wr3, df1.loc[wr3, 'cost'], int(df1.loc[wr3, 'proj_score'])))
    new_team['te'] = str((te, df1.loc[te, 'cost'], int(df1.loc[te, 'proj_score'])))
    new_team['defense'] = str((defense, df2.loc[defense, 'cost'], int(df2.loc[defense, 'proj_score'])))
    new_team['flex'] = str((flex, df1.loc[flex, 'cost'], int(df1.loc[flex, 'proj_score'])))

    #calculate
    for pos in team_list:
        cost += df1.loc[pos, 'cost']
        proj_score += df1.loc[pos, 'proj_score']

    cost += df2.loc[defense, 'cost']
    proj_score += df2.loc[defense, 'proj_score']

    new_team['cost'] = cost
    new_team['proj_score'] = proj_score

    new_team_df = pd.DataFrame(new_team, index = [0])
    return new_team_df




# fn to calculate the score for a total team: takes in the team dataframe
def team_score(team):
    n = team.shape[0]
    team_score = 0

    for player in range(n):
        team_score += team.loc[player, 'proj_score']

    return team_score

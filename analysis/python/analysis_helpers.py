import os
import pandas as pd
import numpy as np
from numpy import shape

import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
sns.set_context('poster')
colors = sns.color_palette("cubehelix", 5)

###############################################################################################
################### HELPERS FOR grpahical conventions analysis notebook ###########
###############################################################################################


def get_complete_and_valid_games(games,coll,researchers=['A1MMCS8S8CTWKU']):
    '''
    Input: Accepts list of gameIDs that are in the database, and a list of the researcher worker ID's
    Output: Returns list of complete and valid gameID, defined as: 
        (1) complete games (correct number of trials==40)
        (2) there were two real MTurk workers participating (i.e., not a researcher or undefined worker)

    '''
    complete_games = []
    for i, game in enumerate(games):
        num_clicks = coll.find({'$and': [{'gameid':game},{'eventType':'clickedObj'}]}).count()
        ## check to make sure there were two real mturk workers participating who were not researchers
        real_workers = False
        viewer = coll.find({'$and': [{'gameid':game},{'eventType':'clickedObj'}]}).distinct('workerId')
        sketcher = coll.find({'$and': [{'gameid':game},{'eventType':'clickedObj'}]}).distinct('workerId')
        viewer_is_researcher = viewer in researchers
        sketcher_is_researcher = sketcher in researchers  
        try:
            viewer_check = (len(viewer[0])>10) & len(viewer)==1 ## length of workerID string should be long enough & there should be exactly one viewer
            sketcher_check = (len(sketcher[0])>10) & len(sketcher)==1 ## length of workerID string should be long enough & there should be exactly one viewer    
            if (viewer_check) & (sketcher_check) & (not viewer_is_researcher) & (not sketcher_is_researcher):
                real_workers = True
        except:
            print 'There was something wrong with this game {}'.format(game)

        ## check to make sure there are the correct number of clicked Obj events, which should equal the number of trials in the game   
        finished_game = False
        if num_clicks == 40:
            finished_game = True

        ## now if BOTH of the above conditions are true, bother to analyze them
        if (real_workers) & (finished_game):
            complete_games.append(game)
    print 'There are {} complete games in total.'.format(len(complete_games))
    return complete_games
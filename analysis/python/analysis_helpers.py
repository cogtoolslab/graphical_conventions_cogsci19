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

def convert_numeric(X,column_id):
    ## make numeric types for aggregation
    X[column_id] = pd.to_numeric(X[column_id])
    return X

def get_complete_and_valid_games(games,
                                 coll,                                 
                                 researchers,
                                 tolerate_undefined_worker=False):
    '''
    Input: 
        -- games: a list of gameIDs that are in the database, and a list of the researcher worker ID's
        -- coll: the mongodb collection, e.g., db['3dObjects']['graphical_conventions']
        -- researchers: the list of researchers, which we exclude from our analysis 
        -- tolerate_undefined_worker: *only in debug mode*, we can allow games through that have undefined worker ID's
    Output: Returns list of complete and valid gameID, defined as: 
        -- a complete game (correct number of trials==40)
        -- there were two real MTurk workers participating (i.e., not a researcher or undefined worker)

    '''
    complete_games = []
    for i, game in enumerate(games):
        num_clicks = coll.find({'$and': [{'gameid':game},{'eventType':'clickedObj'}]}).count()
        ## check to make sure there were two real mturk workers participating who were not researchers
        real_workers = False
        viewer = coll.find({'$and': [{'gameid':game},{'eventType':'clickedObj'}]}).distinct('workerId')
        sketcher = coll.find({'$and': [{'gameid':game},{'eventType':'stroke'}]}).distinct('workerId')
        viewer_is_researcher = viewer in researchers
        sketcher_is_researcher = sketcher in researchers  
        try:
            viewer_check = (len(viewer[0])>10) & len(viewer)==1 ## length of workerID string should be long enough & there should be exactly one viewer
            sketcher_check = (len(sketcher[0])>10) & len(sketcher)==1 ## length of workerID string should be long enough & there should be exactly one viewer    
            if (viewer_check) & (sketcher_check) & (not viewer_is_researcher) & (not sketcher_is_researcher):
                real_workers = True
            if tolerate_undefined_worker:
                real_workers = True
        except:
            print 'There was something wrong with this game {}'.format(game)

        ## check to make sure there are the correct number of clicked Obj events, which should equal the number of trials in the game   
        finished_game = False
        if num_clicks == 40:
            finished_game = True

        ##print game, viewer_check, sketcher_check, viewer_is_researcher, sketcher_is_researcher, num_clicks
            
        ## now if BOTH of the above conditions are true, bother to analyze them
        if (real_workers) & (finished_game):
            complete_games.append(game)
    print 'There are {} complete games in total.'.format(len(complete_games))
    return complete_games


def plot_across_repeats(D, # the dataframe
                        var='drawDuration', # the variable you want to see plotted against numRepts 
                        limit=10,
                        save_plot=False,
                        plot_dir='./plots'): # the y range for the plot 

    '''
    purpose: get timeseries (with error band) for some behavioral measure of interest across repetitions
    note: This only applies to the "repeated" objects.
          We are currently aggregating across objects within a repetition within subject, so the error bands
          only reflect between-subject variability.
    input:
            D: the group dataframe
            var: the variable you want to see plotted against numReps, e.g., 'drawDuration'
            limit: the y range for the plot 
            save_plot: do you want to save the plot?
            plot_dir: path to where to save out the plot
    output: another dataframe?
            a timeseries plot    
    '''    
    
    ## first convert variable type so we are allowed to do arithmetic on it
    D = convert_numeric(D,var)
    
    ## collapsing across objects within repetition (within pair) 
    ## and only aggregating repeated trials into this sub-dataframe
    _D0 = D[D['condition']=='repeated']
    D0 = _D0.groupby(['gameID','repetition','condition'])[var].mean()
    D0 = D0.reset_index()  
    
    ## make sure that the number of timepoints now per gameID is equal to the number of repetitions in the game
    num_reps = len(np.unique(D.repetition.values))
    assert D0.groupby('gameID')['gameID'].count()[0]==num_reps    

    fig = plt.figure(figsize=(6,6))
    ## repeated condition
    sns.tsplot(data=D0,
               time='repetition',
               unit='gameID',
               value=var)
    plt.ylim([0,limit])
    plt.xticks(np.arange(np.max(D0['repetition'])+1))
    plt.savefig(os.path.join(plot_dir,'timeseries_across_reps_{}.pdf'.format(var)))

    return D0
    
    
def compare_conditions_prepost(D, # the dataframe
                        var='drawDuration', # the variable you want to see plotted against numRepts 
                        limit=10,
                        save_plot=False,
                        plot_dir='./plots'): # the y range for the plot 
    
    '''
    purpose: compare repeated and control conditions in the PRE and POST phases with error bars
    note: We are currently aggregating across objects within a repetition within subject, so the error bars
          only reflect between-subject variability.
    input:
            D: the group dataframe
            var: the variable you want to see plotted against numReps, e.g., 'drawDuration'
            limit: the y range for the plot 
            save_plot: do you want to save the plot?
            plot_dir: path to where to save out the plot
    output: another dataframe?
            a point plot    
    '''
    
    _D1 = D[D['phase']!='repeated'] ## exclude "repetition-phase" trials
    D1 = _D1.groupby(['gameID','phase','condition'])[var].mean()
    D1 = D1.reset_index()    
    
    plt.figure(figsize=(6,6))
    sns.pointplot(data=D1,
             x='phase',
             y='drawDuration',
             hue='condition',
             order=['pre','post'])    
    plt.ylim([0,limit])
    plt.savefig(os.path.join(plot_dir,'timeseries_across_reps_{}.pdf'.format(var))) 
    return D1    
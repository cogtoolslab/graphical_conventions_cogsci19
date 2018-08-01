import os
import pandas as pd
import numpy as np
from numpy import shape
from PIL import Image
import base64

import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
sns.set_context('poster')
colors = sns.color_palette("cubehelix", 5)

###############################################################################################
################### HELPERS FOR graphical conventions analysis notebook ####################################
###############################################################################################

#Dictionaries to convert between objects and categories 

OBJECT_TO_CATEGORY_run1 = {
    'basset': 'dog', 'beetle': 'car', 'bloodhound': 'dog', 'bluejay': 'bird',
    'bluesedan': 'car', 'bluesport': 'car', 'brown': 'car', 'bullmastiff': 'dog',
    'chihuahua': 'dog', 'crow': 'bird', 'cuckoo': 'bird', 'doberman': 'dog',
    'goldenretriever': 'dog', 'hatchback': 'car', 'inlay': 'chair', 'knob': 'chair',
    'leather': 'chair', 'nightingale': 'bird', 'pigeon': 'bird', 'pug': 'dog',
    'redantique': 'car', 'redsport': 'car', 'robin': 'bird', 'sling': 'chair',
    'sparrow': 'bird', 'squat': 'chair', 'straight': 'chair', 'tomtit': 'bird',
    'waiting': 'chair', 'weimaraner': 'dog', 'white': 'car', 'woven': 'chair',
}
CATEGORY_TO_OBJECT_run1 = {
    'dog': ['basset', 'bloodhound', 'bullmastiff', 'chihuahua', 'doberman', 'goldenretriever', 'pug', 'weimaraner'],
    'car': ['beetle', 'bluesedan', 'bluesport', 'brown', 'hatchback', 'redantique', 'redsport', 'white'],
    'bird': ['bluejay', 'crow', 'cuckoo', 'nightingale', 'pigeon', 'robin', 'sparrow', 'tomtit'],
    'chair': ['inlay', 'knob', 'leather', 'sling', 'squat', 'straight', 'waiting', 'woven'],
}

OBJECT_TO_CATEGORY_run2 = {
    'deck_00':'deck', 'deck_01':'deck', 'deck_02':'deck', 'deck_03':'deck', 'deck_04':'deck', 'deck_05':'deck',
     'deck_06':'deck', 'deck_07':'deck', 'deck_08':'deck', 'deck_09':'deck', 'deck_10':'deck', 'deck_11':'deck',
     'dining_00':'dining','dining_01':'dining','dining_02':'dining','dining_03':'dining','dining_04':'dining','dining_05':'dining',
    'dining_06':'dining','dining_07':'dining','dining_08':'dining','dining_09':'dining','dining_10':'dining','dining_11':'dining',
    'armchair_00':'armchair','armchair_01':'armchair','armchair_02':'armchair','armchair_03':'armchair','armchair_04':'armchair','armchair_05':'armchair',
    'armchair_06':'armchair','armchair_07':'armchair','armchair_08':'armchair','armchair_09':'armchair','armchair_10':'armchair','armchair_11':'armchair',
    'waiting_00':'waiting', 'waiting_01':'waiting', 'waiting_02':'waiting', 'waiting_03':'waiting', 'waiting_04':'waiting', 'waiting_05':'waiting',
     'waiting_06':'waiting', 'waiting_07':'waiting', 'waiting_08':'waiting', 'waiting_09':'waiting', 'waiting_10':'waiting', 'waiting_11':'waiting'
}

CATEGORY_TO_OBJECT_run2 = {
    'deck': ['deck_00', 'deck_01', 'deck_02', 'deck_03', 'deck_04', 'deck_05', 'deck_06', 'deck_07', 'deck_08', 'deck_09', 'deck_10', 'deck_11'],
    'dining': ['dining_00', 'dining_01','dining_02','dining_03','dining_04','dining_05','dining_06','dining_07','dining_08','dining_09','dining_10','dining_11'],
    'armchair': ['armchair_00','armchair_01','armchair_02','armchair_03','armchair_04','armchair_05','armchair_06','armchair_07','armchair_08','armchair_09','armchair_10','armchair_11'],
    'waiting': ['waiting_00','waiting_01','waiting_02','waiting_03','waiting_04','waiting_05','waiting_06','waiting_07','waiting_08','waiting_09','waiting_10','waiting_11']
}


################################################################################################

### Subhelper 0

def convert_numeric(X,column_id):
    ## make numeric types for aggregation
    X[column_id] = pd.to_numeric(X[column_id])
    return X

###  Subhelper 1

def collapse_within_repetition(D, var, condition, numReps):
    _D = D[D['condition']==condition]
    if condition == 'repeated':
        return (_D.groupby(['gameID','repetition','condition'])[var].mean()).reset_index()
    else: 
        newD = (_D.groupby(['gameID','repetition','condition'])[var].mean()).reset_index()
        newD.repetition = newD.repetition.replace(1, numReps-1)
        return newD
    
###  Subhelper 2
    
def plot_repeated_control(D_repeated, D_control, var, ax, numReps, D):
    sns.tsplot(data=D_repeated,
           time='repetition',
           unit='gameID',
           value=var,
           ax=ax)

    sns.tsplot(data=D_control,
               time='repetition',
               unit='gameID',
               value=var,
               err_style='ci_bars',
               interpolate=False,
               ax=ax,
               color='r')
    
    #mean_accuracy_list = []
    #for i in range(0,6):
    #    outcome_list = (D.loc[D['repetition'] == i])['outcome']
    #    mean_accuracy = (sum(outcome_list) / float(len(outcome_list)))*5
    #    mean_accuracy_list.append(mean_accuracy)
    #D_mean = pd.DataFrame()
    #D_mean['meanAccuracy'] = mean_accuracy_list
    #D_mean['repetition'] = range(0,6)
    #plt.figure(figsize=(6,6))
    
    #sns.tsplot(data=D_mean,
     #        time='repetition',
      #       value='meanAccuracy',
       #      ax=ax)    
    # plt.ylim([0,limit])
    
    ax.set(xlim=(-0.5, numReps - 0.5), xticks=range(0,8))

###############################################################################################

def get_complete_and_valid_games(games,
                                 coll,       
                                 iterationName,
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
        num_clicks = coll.find({'$and': [{'gameid':game},{'eventType':'clickedObj'},{'iterationName':iterationName}]}).count()
        ## check to make sure there were two real mturk workers participating who were not researchers
        real_workers = False
        viewer = coll.find({'$and': [{'gameid':game},{'eventType':'clickedObj'},{'iterationName':iterationName}]}).distinct('workerId')
        sketcher = coll.find({'$and': [{'gameid':game},{'eventType':'stroke'},{'iterationName':iterationName}]}).distinct('workerId')
        if viewer == 'A1V2P0JYPD7GM6' or sketcher == 'A1V2P0JYPD7GM6':
            print "A1V2P0JYPD7GM6 did complete HIT"
        if viewer == 'A6FE2ZQNFW12V' or sketcher == 'A6FE2ZQNFW12V':
            print "A6FE2ZQNFW12V did complete HIT"
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
            if (len(game) < 1):
                print 'There was something wrong with this game {}'.format(game)

        ## check to make sure there are the correct number of clicked Obj events, which should equal the number of trials in the game   
        finished_game = False

        if (iterationName == 'run2_chairs1k_size6' or iterationName == 'run3_size6_waiting'):
            if num_clicks == 48:
                finished_game = True
        else:
            if num_clicks == 40:
                finished_game = True
       

        ##print game, viewer_check, sketcher_check, viewer_is_researcher, sketcher_is_researcher, num_clicks
            
        ## now if BOTH of the above conditions are true, bother to analyze them
        if (real_workers) & (finished_game):
            complete_games.append(game)
    print 'There are {} complete games in total.'.format(len(complete_games))
    return complete_games



###############################################################################################

### normalizing dataframe in terms of numstrokes
def grand_mean_normalize(D_normalized, dv, _complete_games):

    grand_mean = float(sum(list(D_normalized[dv])) / float(len(list(D_normalized[dv]))))
    for g in _complete_games:
        D_subject = D_normalized[D_normalized['gameID'] == g]
        subject_mean = float(sum(list(D_subject[dv])) / float(len(list(D_subject[dv]))))
        for i, d in D_normalized.iterrows():
            if d['gameID'] == g:
                D_normalized.ix[i, dv] = float(d[dv]  - subject_mean + grand_mean)
                
    return D_normalized

###############################################################################################

def ts_repeated(D, # the dataframe
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
               value=var,
               ci=68)
    plt.xlim([-0.5,7.5])
    plt.ylim([0,limit])
    plt.xticks(np.arange(np.max(D0['repetition'])+1))
    plt.savefig(os.path.join(plot_dir,'timeseries_across_reps_{}.pdf'.format(var)))

    return D0

###############################################################################################

def ts_repeated_control(D, # the dataframe
                        var='drawDuration', # the variable you want to see plotted against numRepts 
                        numReps = 8,
                        upper_limit=10,
                        lower_limit = 2,
                        save_plot=False,
                        plot_dir='./plots'): # the y range for the plot 
    
    '''
    purpose: get timeseries (with error band) for some behavioral measure of interest across repetitions
    note: This applies to BOTH repeated and control objects 
          We are currently aggregating across objects within a repetition within subject, so the error bands
          only reflect between-subject variability.
    input:
            D: the group dataframe
            var: the variable you want to see plotted against numReps, e.g., 'drawDuration'
            limit: the y range for the plot 
            save_plot: do you want to save the plot?
            plot_dir: path to where to save out the plot
    output: 
            a timeseries plot    
    '''  
    
    ## first convert variable type so we are allowed to do arithmetic on it
    D = convert_numeric(D,var)

    ## collapsing across objects within repetition (within pair) 
    ## and only aggregating repeated trials into this sub-dataframe
    _D0 = D[D['condition']=='repeated']
    D0 = _D0.groupby(['gameID','repetition','condition'])[var].mean()
    D0 = D0.reset_index()  
    
    ## and only aggregating control trials into this sub-dataframe
    _D1 = D[D['condition']=='control']
    D1 = _D1.groupby(['gameID','repetition','condition'])[var].mean()
    D1 = D1.reset_index()  
    D1.repetition = D1.repetition.replace(1, numReps-1) # rescale control repetitions 

    ## make sure that the number of timepoints now per gameID is equal to the number of repetitions in the game
    num_reps = len(np.unique(D.repetition.values))
    assert D0.groupby('gameID')['gameID'].count()[0]==num_reps    

    fig, ax = plt.subplots()
    
    ## repeated condition
    sns.tsplot(data=D0,
               time='repetition',
               unit='gameID',
               value=var,
               ci=68,
               ax=ax)
    
    ## control condition 
    sns.tsplot(data=D1,
               time='repetition',
               unit='gameID',
               value=var,
               ci=68,
               err_style='ci_bars',
               interpolate=False,
               ax=ax,
               color='r')
    
##    mean_accuracy_list = []
##    for i in range(0,6):
##        outcome_list = (D.loc[D['repetition'] == i])['outcome']
##       mean_accuracy = (sum(outcome_list) / float(len(outcome_list)))*10
 #       mean_accuracy_list.append(mean_accuracy)
    #D_mean = pd.DataFrame()
   # D_mean['meanAccuracy'] = mean_accuracy_list
    #D_mean['repetition'] = range(0,6)
    #plt.figure(figsize=(6,6))
    
    #sns.tsplot(data=D_mean,
    #         time='repetition',
     #        value='meanAccuracy',
       #      ax=ax)    
    # plt.ylim([0,limit])
    
    plt.xlim([-0.5, numReps - 0.5])
    plt.ylim([lower_limit, upper_limit])
    plt.xticks(np.arange(0, numReps, step=1))
    plt.savefig(os.path.join(plot_dir,'timeseries_across_reps_{}.pdf'.format(var)))
    
###############################################################################################

def ts_grid_repeated_control(D, 
                                      var0, var1, var2, var3,
                                       numReps=8,
                                      save_plot=False,
                                      plot_dir='./plots'):
    
    '''
    purpose: get timeseries (with error band) for 4 behavioral measures of interest across repetitions: 
                drawDuration, numStrokes (actions), numCurvesPerSketch (total splines), and numCurvesPerStroke (stroke complexity)
               
    note: This applies to BOTH repeated and control objects. 
          We are currently aggregating across objects within a repetition within subject, so the error bands
          only reflect between-subject variability.
          
    input:
            D: the group dataframe
            save_plot: do you want to save the plot?
            plot_dir: path to where to save out the plot
            
    output: 
            a timeseries plot    
    '''  
    
    D = convert_numeric(convert_numeric(convert_numeric(convert_numeric(D,var0),var1),var2),var3) 
    
    D0_repeated = collapse_within_repetition(D, var0, 'repeated', numReps)
    D1_repeated = collapse_within_repetition(D, var1, 'repeated', numReps)
    D2_repeated = collapse_within_repetition(D, var2, 'repeated', numReps)
    D3_repeated = collapse_within_repetition(D, var3, 'repeated', numReps)
    D0_control = collapse_within_repetition(D, var0, 'control', numReps)
    D1_control = collapse_within_repetition(D, var1, 'control', numReps)
    D2_control = collapse_within_repetition(D, var2, 'control', numReps)
    D3_control = collapse_within_repetition(D, var3, 'control', numReps)

    ## make sure that the number of timepoints now per gameID is equal to the number of repetitions in the game
    num_reps = len(np.unique(D.repetition.values))
    assert D0_repeated.groupby('gameID')['gameID'].count()[0]==num_reps    

    #fig = plt.figure(figsize=(12,12))
    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(nrows=2, ncols=2, figsize=(12,8))

    plot_repeated_control(D0_repeated, D0_control, var0, ax0, numReps, D)
    plot_repeated_control(D1_repeated, D1_control, var1, ax1, numReps, D)
    plot_repeated_control(D2_repeated, D2_control, var2, ax2, numReps, D)
    plot_repeated_control(D3_repeated, D3_control, var3, ax3, numReps, D)

    ax0.set_ylim([2, 8])
    ax1.set_ylim([3, 16])
    ax2.set_ylim([8, 32])
    ax3.set_ylim([0, 0.05])
    
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    
    
###############################################################################################
    
def line_grid_individual(D, 
                                      var0, var1, var2, var3,
                                       numReps=8,
                                      save_plot=False,
                                      plot_dir='./plots'):
    
    if numReps == 8:
        set_size = 4
    if numReps == 6:
        set_size = 6

    D = convert_numeric(convert_numeric(convert_numeric(convert_numeric(D,var0),var1),var2),var3) 

    ## collapsing across objects within repetition (within pair) 
    ## and only aggregating repeated trials into this sub-dataframe
    D0 = collapse_within_repetition(D, var0, 'repeated', set_size)
    D1 = collapse_within_repetition(D, var1, 'repeated', set_size)
    D2 = collapse_within_repetition(D, var2, 'repeated', set_size)
    D3 = collapse_within_repetition(D, var3, 'repeated', set_size)

    #fig = plt.figure(figsize=(12,12))
    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(nrows=2, ncols=2, figsize=(10,10))

    ## make sure that the number of timepoints now per gameID is equal to the number of repetitions in the game
    num_reps = len(np.unique(D.repetition.values))
    assert D0.groupby('gameID')['gameID'].count()[0]==num_reps    

    sns.lineplot(data=D0,
               x='repetition',
               hue='gameID',
               units='gameID',
               y=var0,
               estimator = None,
               ax=ax0,
               legend = False)

    sns.lineplot(data=D1,
               x='repetition',
               hue='gameID',
               units='gameID',
               y=var1,
               estimator = None,
               ax=ax1,
               legend = False)

    sns.lineplot(data=D2,
               x='repetition',
               hue='gameID',
               units='gameID',
               y=var2,
               estimator = None,
               ax=ax2,
               legend = False)

    sns.lineplot(data=D3,
               x='repetition',
               hue='gameID',
               units='gameID',
               y=var3,
               estimator = None,
               ax=ax3)

    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    #plt.xticks(np.arange(0, numReps, step=1))
    ax0.set_xticks(np.arange(numReps))
    ax1.set_xticks(np.arange(numReps))
    ax2.set_xticks(np.arange(numReps))
    ax3.set_xticks(np.arange(numReps))
    ax0.set_xticklabels(np.arange(numReps))
    ax1.set_xticklabels(np.arange(numReps))
    ax2.set_xticklabels(np.arange(numReps))
    ax3.set_xticklabels(np.arange(numReps))
    ax0.set_ylim([1, 14])
    ax1.set_ylim([3, 20])
    ax2.set_ylim([8, 50])
    ax3.set_ylim([0.01, 0.07])
    ax3.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

###############################################################################################

def ts_grid_repeated(D, # the dataframe
                        var0, var1, var2, var3,
                        save_plot=False,
                        plot_dir='./plots'): # the y range for the plot 

    '''
    purpose: get timeseries (with error band) for 4 behavioral measures of interest across repetitions: 
                drawDuration, numStrokes (actions), numCurvesPerSketch (total splines), and numCurvesPerStroke (stroke complexity)
               
    note: This only applies to the "repeated" objects.
          We are currently aggregating across objects within a repetition within subject, so the error bands
          only reflect between-subject variability.
          
    input:
            D: the group dataframe
            save_plot: do you want to save the plot?
            plot_dir: path to where to save out the plot
            
    output: 
            a timeseries plot    
    '''  

    D = convert_numeric(convert_numeric(convert_numeric(convert_numeric(D,var0),var1),var2),var3) 

    ## collapsing across objects within repetition (within pair) 
    ## and only aggregating repeated trials into this sub-dataframe
    D0 = collapse_within_repetition(D, var0, 'repeated')
    D1 = collapse_within_repetition(D, var1, 'repeated')
    D2 = collapse_within_repetition(D, var2, 'repeated')
    D3 = collapse_within_repetition(D, var3, 'repeated')
    
    #fig = plt.figure(figsize=(12,12))
    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(nrows=2, ncols=2, figsize=(10,5))

    ## make sure that the number of timepoints now per gameID is equal to the number of repetitions in the game
    num_reps = len(np.unique(D.repetition.values))
    assert D0.groupby('gameID')['gameID'].count()[0]==num_reps    

    sns.lineplot(data=D0,
               x='repetition',
               hue='gameID',
               unit='gameID',
               y=var0,
               ax=ax0)

    sns.lineplot(data=D1,
               x='repetition',
               hue='gameID',
               unit='gameID',
               y=var1,
               ax=ax1)

    sns.lineplot(data=D2,
               x='repetition',
               hue='gameID',
               unit='gameID',
               y=var2,
               ax=ax2)

    sns.lineplot(data=D3,
               x='repetition',
               hue='gameID',
               unit='gameID',
               y=var3,
               ax=ax3)

    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    plt.xticks(np.arange(np.max(D0['repetition'])+1))
    
###############################################################################################

def compare_conditions_prepost(D, # the dataframe
                        var='outcome', # the variable you want to see plotted against numRepts 
                        lower_limit = 2,
                        upper_limit=10,
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
             y=var,
             hue='condition',
             order=['pre','post'])    
    plt.ylim([lower_limit,upper_limit])
    #plt.savefig(os.path.join(plot_dir,'timeseries_across_reps_{}.pdf'.format(var))) 
    return D1    

###############################################################################################

def print_repeated_sketches(D,
                                     complete_games,
                                     sketch_dir): 
    
    _valid_gameids = complete_games

    for g in _valid_gameids:
        print 'Printing out sketches from game: ' + g
        trial_types = ['repeated']
        for tt in trial_types:
            _D = D[(D.condition=='repeated') & (D.gameID==g)]
            all_targs = np.unique(_D.target.values) ## use this later to name the file
            _D = _D.sort_values(by=['target','repetition'])
            _i = 1
            textsize=12
            fig = plt.figure(figsize=(16,6))
            for i,_d in _D.iterrows():
                imgData = _d['png']
                filestr = base64.b64decode(imgData)
                fname = 'sketch.png'
                with open(fname, "wb") as fh:
                    fh.write(imgData.decode('base64'))
                textsize = 16
                # first plot the target
                im = Image.open(fname)
                p = plt.subplot(4,8,_i)
                plt.imshow(im)
                sns.set_style('white')
                k = p.get_xaxis().set_ticklabels([])
                k = p.get_yaxis().set_ticklabels([])
                k = p.get_xaxis().set_ticks([])
                k = p.get_yaxis().set_ticks([]) 
                outcome = _d['outcome']
                category = _d['category']
                if outcome == 1:
                    sides = ['bottom','top','right','left']
                    for s in sides:
                        p.spines[s].set_color((0.4,0.8,0.4))
                        p.spines[s].set_linewidth(4)                               
                else:
                    sides = ['bottom','top','right','left']
                    for s in sides:
                        p.spines[s].set_color((0.9,0.2,0.2))
                        p.spines[s].set_linewidth(4)    
                if (_i-1 < 8) & (tt in 'repeated'): 
                    plt.title('rep ' + str(_d['repetition']) ,fontsize=textsize)
                if (_i-1)%8==0:
                    plt.ylabel(_d['target'] ,fontsize=textsize)

                _i  = _i + 1

            filepath = os.path.join(sketch_dir,'repeated','{}_{}.pdf'.format(g,category))                                                                
            if not os.path.exists(os.path.join(sketch_dir,'repeated')):
                os.makedirs(os.path.join(sketch_dir,'repeated'))
            plt.tight_layout()
            #plt.savefig(os.path.join(sketch_dir,'repeated',filepath))
            #plt.close(fig)
           
        
###############################################################################################

def print_control_sketches(D,
                                   complete_games,
                                   sketch_dir): 

    for g in complete_games:
        print 'Printing out sketches from game: ' + g
        trial_types = ['control']
        for tt in trial_types:
            _D = D[(D.condition=='control') & (D.gameID==g)]
            all_targs = np.unique(_D.target.values) ## use this later to name the file
            _D = _D.sort_values(by=['target','repetition'])
            _i = 1
            textsize=12
            fig = plt.figure(figsize=(16,6))
            for i,_d in _D.iterrows():
                imgData = _d['png']
                filestr = base64.b64decode(imgData)
                fname = 'sketch.png'
                with open(fname, "wb") as fh:
                    fh.write(imgData.decode('base64'))
                textsize = 16
                # first plot the target
                im = Image.open(fname)
                p = plt.subplot(4,2,_i)
                plt.imshow(im)
                sns.set_style('white')
                k = p.get_xaxis().set_ticklabels([])
                k = p.get_yaxis().set_ticklabels([])
                k = p.get_xaxis().set_ticks([])
                k = p.get_yaxis().set_ticks([]) 
                outcome = _d['outcome']
                category = _d['category']
                if outcome == 1:
                    sides = ['bottom','top','right','left']
                    for s in sides:
                        p.spines[s].set_color((0.4,0.8,0.4))
                        p.spines[s].set_linewidth(4)                               
                else:
                    sides = ['bottom','top','right','left']
                    for s in sides:
                        p.spines[s].set_color((0.9,0.2,0.2))
                        p.spines[s].set_linewidth(4)    
                if (_i-1 < 2) & (tt in 'control'): 
                    plt.title('rep ' + str(_d['repetition']) ,fontsize=textsize)
                if (_i-1)%2==0:
                    plt.ylabel(_d['target'] ,fontsize=textsize)

                _i  = _i + 1

            filepath = os.path.join(sketch_dir,'control','{}_{}.pdf'.format(g,category))     
            if not os.path.exists(os.path.join(sketch_dir,'control')):
                os.makedirs(os.path.join(sketch_dir,'control'))
            #plt.savefig(os.path.join(sketch_dir,'control',filepath))
            #plt.close(fig)
            
###############################################################################################

def print_repeated_actual(D,
                                   complete_games,
                                   set_size): 
    
    if (set_size == 4):
        index = list(range(1, 37))
        new_index = filter(lambda x: x%9!=0, index)
        numReps = 8
    if (set_size == 6):
        index = list(range(1, 43))
        new_index = filter(lambda x: x%7!=0, index)
        numReps = 6
    
    for g in complete_games:
        print 'Printing out sketches from game: ' + g
        trial_types = ['repeated']
        for tt in trial_types:
            _D = D[(D.condition=='repeated') & (D.gameID==g)]
            all_targs = np.unique(_D.target.values) ## use this later to name the file
            _D = _D.sort_values(by=['target','repetition'])
            _i = 0
            textsize=12
            if set_size == 4:
                fig = plt.figure(figsize=(20,9))
            if set_size == 6:
                fig = plt.figure(figsize=(10,10))
            for i,_d in _D.iterrows():
                true_index = new_index[_i]
                if _i % numReps == 0:
                    target = _d['target']
                    dir_path = 'chairs1k_pilot'
                    png_name = target + '.png'
                    path = os.path.join(dir_path, png_name)
                    im = Image.open(path)
                    cropped_im = im.crop((350, 150, 600, 400))
                    p = plt.subplot(set_size,numReps+1,true_index+numReps)
                    plt.imshow(cropped_im)
                    sns.set_style('white')
                    k = p.get_xaxis().set_ticklabels([])
                    k = p.get_yaxis().set_ticklabels([])
                    k = p.get_xaxis().set_ticks([])
                    k = p.get_yaxis().set_ticks([]) 
                imgData = _d['png']
                filestr = base64.b64decode(imgData)
                fname = 'sketch.png'
                with open(fname, "wb") as fh:
                    fh.write(imgData.decode('base64'))
                textsize = 16
                # first plot the target
                im = Image.open(fname)
                p = plt.subplot(set_size,numReps+1,true_index)
                plt.imshow(im)
                sns.set_style('white')
                k = p.get_xaxis().set_ticklabels([])
                k = p.get_yaxis().set_ticklabels([])
                k = p.get_xaxis().set_ticks([])
                k = p.get_yaxis().set_ticks([]) 
                outcome = _d['outcome']
                category = _d['category']
                if outcome == 1:
                    sides = ['bottom','top','right','left']
                    for s in sides:
                        p.spines[s].set_color((0.4,0.8,0.4))
                        p.spines[s].set_linewidth(4)                               
                else:
                    sides = ['bottom','top','right','left']
                    for s in sides:
                        p.spines[s].set_color((0.9,0.2,0.2))
                        p.spines[s].set_linewidth(4)    
                if (_i < numReps) & (tt in 'repeated'): 
                    plt.title('rep ' + str(_d['repetition']) ,fontsize=textsize)
                if _i%numReps==0:
                    plt.ylabel(_d['target'] ,fontsize=textsize)
                _i  = _i + 1

        #filepath = os.path.join(sketch_dir,'repeated','{}_{}.pdf'.format(g,category))                                                                
        #if not os.path.exists(os.path.join(sketch_dir,'repeated')):
       #     os.makedirs(os.path.join(sketch_dir,'repeated'))
        plt.tight_layout()
        #plt.savefig(os.path.join(sketch_dir,'control',filepath))
            #plt.close(fig)

###############################################################################################       

def print_repeated_control(D,
                                   complete_games,
                                   set_size): 
    
    if (set_size == 4):
        index = list(range(1, 37))
        new_index = filter(lambda x: x%9!=0, index)
        numReps = 8
    if (set_size == 6):
        index = list(range(1, 43))
        new_index = filter(lambda x: x%7!=0, index)
        numReps = 6
    
    for g in complete_games:
        print 'Printing out sketches from game: ' + g
        trial_types = ['repeated']
        for tt in trial_types:
            _D = D[(D.condition=='repeated') & (D.gameID==g)]
            D_ = D[(D.condition=='control') & (D.gameID==g)]
            all_targs = np.unique(_D.target.values) ## use this later to name the file
            _D = _D.sort_values(by=['target','repetition'])
            _i = 0
            control_index = 0
            textsize=12
            
            if set_size == 4:
                fig = plt.figure(figsize=(16,6))
            if set_size == 6:
                fig = plt.figure(figsize=(10,10))
                
            for i,_d in _D.iterrows():
                true_index = new_index[_i]
                if _i % numReps == 0:
                    # plot last of control sketch 
                    target = _d['target']
                    D__ = D_[D_.phase == 'post']
                    imgData = D__['png'].iloc[control_index]
                    filestr = base64.b64decode(imgData)
                    fname = 'sketch.png'
                    with open(fname, "wb") as fh:
                        fh.write(imgData.decode('base64'))
                    textsize = 12
                    # first plot the target
                    im = Image.open(fname)
                    p = plt.subplot(set_size,numReps+1,true_index+numReps)
                    plt.imshow(im)
                    if (_i < numReps):
                        plt.title('control' ,fontsize=textsize)
                    sns.set_style('white')
                    k = p.get_xaxis().set_ticklabels([])
                    k = p.get_yaxis().set_ticklabels([])
                    k = p.get_xaxis().set_ticks([])
                    k = p.get_yaxis().set_ticks([]) 
                    outcome = D__['outcome'].iloc[control_index]
                    if outcome == 1:
                        sides = ['bottom','top','right','left']
                        for s in sides:
                            p.spines[s].set_color((0.4,0.8,0.4))
                            p.spines[s].set_linewidth(4)                               
                    else:
                        sides = ['bottom','top','right','left']
                        for s in sides:
                            p.spines[s].set_color((0.9,0.2,0.2))
                            p.spines[s].set_linewidth(4)    
                imgData = _d['png']
                filestr = base64.b64decode(imgData)
                fname = 'sketch.png'
                with open(fname, "wb") as fh:
                    fh.write(imgData.decode('base64'))
                textsize = 16
                # first plot the target
                im = Image.open(fname)
                p = plt.subplot(set_size,numReps+1,true_index)
                plt.imshow(im)
                sns.set_style('white')
                k = p.get_xaxis().set_ticklabels([])
                k = p.get_yaxis().set_ticklabels([])
                k = p.get_xaxis().set_ticks([])
                k = p.get_yaxis().set_ticks([]) 
                outcome = _d['outcome']
                category = _d['category']
                if outcome == 1:
                    sides = ['bottom','top','right','left']
                    for s in sides:
                        p.spines[s].set_color((0.4,0.8,0.4))
                        p.spines[s].set_linewidth(4)                               
                else:
                    sides = ['bottom','top','right','left']
                    for s in sides:
                        p.spines[s].set_color((0.9,0.2,0.2))
                        p.spines[s].set_linewidth(4)    
                if (_i < numReps) & (tt in 'repeated'): 
                    plt.title('rep ' + str(_d['repetition']) ,fontsize=textsize)
                if _i%numReps==0:
                    plt.ylabel(_d['target'] ,fontsize=textsize)
                    control_index = control_index + 1

                _i  = _i + 1

        #filepath = os.path.join(sketch_dir,'repeated','{}_{}.pdf'.format(g,category))                                                                
        #if not os.path.exists(os.path.join(sketch_dir,'repeated')):
        #    os.makedirs(os.path.join(sketch_dir,'repeated'))
        plt.tight_layout()

###############################################################################################       
            
def get_confusion_matrix(D, category, set_size):
    obj_list = []
    objlist = CATEGORY_TO_OBJECT_run2[category]
    for obj in objlist[:set_size*2]:
        obj_list.append(obj)

    ## initialize confusion matrix 
    confusion = np.zeros((len(obj_list), len(obj_list)))

    ## generate confusion matrix by incrementing each cell 
    for i, d in D.iterrows():
        if d['category'] == category:
            targ_ind = obj_list.index(d['target'])
            chosen_ind = obj_list.index(d['response'])
            confusion[targ_ind, chosen_ind] += 1
    
    ## normalize confusion matrix 
    normed = np.zeros((len(obj_list), len(obj_list)))
    for i in np.arange(len(confusion)):
        normed[i,:] = confusion[i,:]/np.sum(confusion[i,:])
            
    ## plot confusion matrix 
    from matplotlib import cm
    fig = plt.figure(figsize=(8,8))
    ax = plt.subplot(111)
    cax = ax.matshow(normed,vmin=0,vmax=1,cmap=cm.viridis)
    plt.xticks(range(len(normed)), obj_list, fontsize=12,rotation='vertical')
    plt.yticks(range(len(normed)), obj_list, fontsize=12)
    plt.colorbar(cax,shrink=0.8)
    plt.tight_layout()
    #plt.savefig('./plots/confusion_matrix_all.pdf')
    #plt.close(fig)
   
    
    
###############################################################################################
            
def get_confusion_matrix(D, category, set_size):
    obj_list = []
    objlist = CATEGORY_TO_OBJECT_run2[category]
    for obj in objlist[:set_size*2]:
        obj_list.append(obj)

    ## initialize confusion matrix 
    confusion = np.zeros((len(obj_list), len(obj_list)))

    ## generate confusion matrix by incrementing each cell 
    for i, d in D.iterrows():
        if d['category'] == category:
            targ_ind = obj_list.index(d['target'])
            chosen_ind = obj_list.index(d['response'])
            confusion[targ_ind, chosen_ind] += 1
    
    ## normalize confusion matrix 
    normed = np.zeros((len(obj_list), len(obj_list)))
    for i in np.arange(len(confusion)):
        normed[i,:] = confusion[i,:]/np.sum(confusion[i,:])
            
    ## plot confusion matrix 
    from matplotlib import cm
    fig = plt.figure(figsize=(8,8))
    ax = plt.subplot(111)
    cax = ax.matshow(normed,vmin=0,vmax=1,cmap=cm.viridis)
    plt.xticks(range(len(normed)), obj_list, fontsize=12,rotation='vertical')
    plt.yticks(range(len(normed)), obj_list, fontsize=12)
    plt.colorbar(cax,shrink=0.8)
    plt.tight_layout()
    #plt.savefig('./plots/confusion_matrix_all.pdf')
    #plt.close(fig)
   
    
    
###############################################################################################   



def get_confusion_matrix_on_rep(D, category, set_size, repetition):

    _D = D[D['condition'] == 'repeated']
    _D = _D[_D['repetition'] == repetition]
    target_list = _D['target'].tolist()
    obj_list_ = []
    obj_list = []
    objlist = CATEGORY_TO_OBJECT_run2[category]
    for obj in objlist[:set_size*2]:
        obj_list_.append(obj)
    for i in obj_list_:
        if i in target_list:
            obj_list.append(i)

    ## initialize confusion matrix 
    confusion = np.zeros((len(obj_list), len(obj_list)))

    ## generate confusion matrix by incrementing each cell 
    for i, d in _D.iterrows():
        if d['category'] == category:
            targ_ind = obj_list.index(d['target'])
            chosen_ind = obj_list.index(d['response'])
            confusion[targ_ind, chosen_ind] += 1

    ## normalize confusion matrix 
    normed = np.zeros((len(obj_list), len(obj_list)))
    for i in np.arange(len(confusion)):
        normed[i,:] = confusion[i,:]/np.sum(confusion[i,:])

    ## plot confusion matrix 
    from matplotlib import cm
    fig = plt.figure(figsize=(8,8))
    ax = plt.subplot(111)
    cax = ax.matshow(normed,vmin=0,vmax=1,cmap=cm.viridis)
    plt.xticks(range(len(normed)), obj_list, fontsize=12,rotation='vertical')
    plt.yticks(range(len(normed)), obj_list, fontsize=12)
    plt.colorbar(cax,shrink=0.8)
    plt.tight_layout()
    #plt.savefig('./plots/confusion_matrix_all.pdf')
    #plt.close(fig)
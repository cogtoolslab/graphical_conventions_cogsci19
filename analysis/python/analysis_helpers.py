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

OBJECT_TO_CATEGORY = {
    'basset': 'dog', 'beetle': 'car', 'bloodhound': 'dog', 'bluejay': 'bird',
    'bluesedan': 'car', 'bluesport': 'car', 'brown': 'car', 'bullmastiff': 'dog',
    'chihuahua': 'dog', 'crow': 'bird', 'cuckoo': 'bird', 'doberman': 'dog',
    'goldenretriever': 'dog', 'hatchback': 'car', 'inlay': 'chair', 'knob': 'chair',
    'leather': 'chair', 'nightingale': 'bird', 'pigeon': 'bird', 'pug': 'dog',
    'redantique': 'car', 'redsport': 'car', 'robin': 'bird', 'sling': 'chair',
    'sparrow': 'bird', 'squat': 'chair', 'straight': 'chair', 'tomtit': 'bird',
    'waiting': 'chair', 'weimaraner': 'dog', 'white': 'car', 'woven': 'chair',
}
CATEGORY_TO_OBJECT = {
    'dog': ['basset', 'bloodhound', 'bullmastiff', 'chihuahua', 'doberman', 'goldenretriever', 'pug', 'weimaraner'],
    'car': ['beetle', 'bluesedan', 'bluesport', 'brown', 'hatchback', 'redantique', 'redsport', 'white'],
    'bird': ['bluejay', 'crow', 'cuckoo', 'nightingale', 'pigeon', 'robin', 'sparrow', 'tomtit'],
    'chair': ['inlay', 'knob', 'leather', 'sling', 'squat', 'straight', 'waiting', 'woven'],
}

################################################################################################

### Subhelper 0

def convert_numeric(X,column_id):
    ## make numeric types for aggregation
    X[column_id] = pd.to_numeric(X[column_id])
    return X

###  Subhelper 1

def collapse_within_repetition(D, var, condition):
    _D = D[D['condition']==condition]
    if condition == 'repeated':
        return (_D.groupby(['gameID','repetition','condition'])[var].mean()).reset_index()
    else: 
        return ((_D.groupby(['gameID','repetition','condition'])[var].mean()).reset_index()).replace(1,7)
    
###  Subhelper 2
    
def plot_repeated_control(D_repeated, D_control, var, ax):
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
    
    ax.set(xlim=(-0.5, 7.5), xticks=range(0,8))

###############################################################################################

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
                        limit=10,
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
    D1 = D1.replace(1, 7) # rescale control repetitions 

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
    
    plt.xlim([-0.5,7.5])
    plt.ylim([0, limit])
    plt.xticks(np.arange(0, 8, step=1))
    plt.savefig(os.path.join(plot_dir,'timeseries_across_reps_{}.pdf'.format(var)))
    
###############################################################################################

def ts_grid_repeated_control(D, 
                                      var0, var1, var2, var3,
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
    
    D0_repeated = collapse_within_repetition(D, var0, 'repeated')
    D1_repeated = collapse_within_repetition(D, var1, 'repeated')
    D2_repeated = collapse_within_repetition(D, var2, 'repeated')
    D3_repeated = collapse_within_repetition(D, var3, 'repeated')
    D0_control = collapse_within_repetition(D, var0, 'control')
    D1_control = collapse_within_repetition(D, var1, 'control')
    D2_control = collapse_within_repetition(D, var2, 'control')
    D3_control = collapse_within_repetition(D, var3, 'control')

    ## make sure that the number of timepoints now per gameID is equal to the number of repetitions in the game
    num_reps = len(np.unique(D.repetition.values))
    assert D0_repeated.groupby('gameID')['gameID'].count()[0]==num_reps    

    #fig = plt.figure(figsize=(12,12))
    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(nrows=2, ncols=2, figsize=(12,5))

    plot_repeated_control(D0_repeated, D0_control, var0, ax0)
    plot_repeated_control(D1_repeated, D1_control, var1, ax1)
    plot_repeated_control(D2_repeated, D2_control, var2, ax2)
    plot_repeated_control(D3_repeated, D3_control, var3, ax3)
    
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)

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
    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(nrows=2, ncols=2, figsize=(12,5))

    ## make sure that the number of timepoints now per gameID is equal to the number of repetitions in the game
    num_reps = len(np.unique(D.repetition.values))
    assert D0.groupby('gameID')['gameID'].count()[0]==num_reps    

    sns.tsplot(data=D0,
               time='repetition',
               unit='gameID',
               value=var0,
               ax=ax0)

    sns.tsplot(data=D1,
               time='repetition',
               unit='gameID',
               value=var1,
               ax=ax1)

    sns.tsplot(data=D2,
               time='repetition',
               unit='gameID',
               value=var2,
               ax=ax2)

    sns.tsplot(data=D3,
               time='repetition',
               unit='gameID',
               value=var3,
               ax=ax3)

    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    plt.xticks(np.arange(np.max(D0['repetition'])+1))
    
###############################################################################################

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
            plt.savefig(os.path.join(sketch_dir,'repeated',filepath))
            plt.close(fig)
        
###############################################################################################

def print_control_sketches(D,
                                   complete_games,
                                   sketch_dir): 
    
    _valid_gameids = complete_games

    for g in _valid_gameids:
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
            plt.savefig(os.path.join(sketch_dir,'control',filepath))
            plt.close(fig)
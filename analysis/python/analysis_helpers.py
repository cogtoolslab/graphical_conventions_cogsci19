from __future__ import division

import os
#import urllib, cStringIO

import json

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
import re
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
    
def plot_repeated_control(D_repeated, D_control, var, ax, numReps):
    df2 = pd.DataFrame([[float('NaN'), 1, 'control', float('NaN')], [float('NaN'), 2, 'control', float('NaN')], [float('NaN'), 3, 'control', float('NaN')], [float('NaN'), 4, 'control', float('NaN')], [float('NaN'), 5, 'control', float('NaN')],[float('NaN'), 6, 'control', float('NaN')]], columns=['gameID', 'repetition', 'condition', var])
    D_control_ = D_control.append(df2)
    sns.lineplot(data=D_repeated,
           x='repetition',
           #units='gameID',
           err_style='bars',
           y=var,
           ax=ax)

    sns.pointplot(data=D_control_,
                   x='repetition',
                   y=var,
                   #units='gameID',
                   err_style='bars',
                   join=False,
                   color='r',
                   dodge=True,
                   errwidth = 3,
                   scale = 0.7,
                   ax=ax)

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
            print("A1V2P0JYPD7GM6 did complete HIT")
        if viewer == 'A6FE2ZQNFW12V' or sketcher == 'A6FE2ZQNFW12V':
            print("A6FE2ZQNFW12V did complete HIT")
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
                print ('There was something wrong with this game {}'.format(game))

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
    print ('There are {} complete games in total.'.format(len(complete_games)))
    return complete_games

###############################################################################################

def generate_dataframe(coll, complete_games, iterationName, results_dir):

    # preprocessing 

    TrialNum = []
    GameID = []
    Condition = []
    Target = []
    Category = []
    Distractor1 = []
    Distractor2 = []
    Distractor3 = []
    Outcome = []
    Response = []
    Repetition = []
    Generalization = []
    Phase = []
    numStrokes = []
    drawDuration = [] # in seconds
    svgStringLength = [] # sum of svg string for whole sketch
    svgStringLengthPerStroke = [] # svg string length per stroke
    numCurvesPerSketch = [] # number of curve segments per sketch
    numCurvesPerStroke = [] # mean number of curve segments per stroke
    svgStringStd = [] # std of svg string length across strokes for this sketch
    Outcome = [] #accuracy (True or False)
    png=[] # the sketch 
    timedOut=[] # True if sketchers didn't draw anything, False o.w.
    meanPixelIntensity=[]

    y = ['3601-5426f18c-ab9f-40c9-b627-e4d09ce1679a'] ## game where trial 4 was repeated 
    _complete_games= [item for item in complete_games if item not in y]
    for i,g in enumerate(_complete_games):
            print( 'Analyzing game {} | {} of {}: '.format(g, i, len(_complete_games)))

            # collection of all clickedObj events in a particular game 
            X = coll.find({ '$and': [{'gameid': g}, {'eventType': 'clickedObj'}]}).sort('time')
            # collection of all stroke events in a particular game 
            Y = coll.find({ '$and': [{'gameid': g}, {'eventType': 'stroke'}]}).sort('time')

            for t in X: # for each clickedObj event
                targetname = t['intendedName']
                category = OBJECT_TO_CATEGORY_run2[targetname]
                Phase.append(t['phase'])
                Repetition.append(t['repetition'])
                distractors = [t['object2Name'],t['object3Name'],t['object4Name']]
                full_list = [t['intendedName'],t['object2Name'],t['object3Name'],t['object4Name']] 
                png.append(t['pngString'])

                #for each stroke event with same trial number as this particular clickedObj event 
                y = coll.find({ '$and': [{'gameid': g}, {'eventType': 'stroke'}, {'trialNum': t['trialNum']}]}).sort('time')
                # have to account for cases in which sketchers do not draw anything 
                if (y.count() == 0):
                    numStrokes.append(float('NaN'))
                    drawDuration.append(float('NaN'))
                    svgStringLength.append(float('NaN'))
                    svgStringLengthPerStroke.append(float('NaN'))
                    numCurvesPerSketch.append(float('NaN'))
                    numCurvesPerStroke.append(float('NaN'))
                    svgStringStd.append(float('NaN'))
                    meanPixelIntensity.append('NaN')
                    timedOut.append(True)
                else: 
                    y = coll.find({ '$and': [{'gameid': g}, {'eventType': 'stroke'}, {'trialNum': t['trialNum']}]}).sort('time')
                    lastStrokeNum = float(y[y.count() - 1]['currStrokeNum']) # get currStrokeNum at last stroke
                    ns = y.count()
                    if not lastStrokeNum == ns:
                        print ("ns: " + str(ns))
                        print ("lastStrokeNum: " + str(lastStrokeNum))

                    numStrokes.append(lastStrokeNum)

                    # calculate drawDuration 
                    startStrokeTime =  float(y[0]['startStrokeTime'])
                    endStrokeTime = float(y[y.count() - 1]['endStrokeTime']) ## took out negative 1 
                    duration = (endStrokeTime - startStrokeTime) / 1000
                    drawDuration.append(duration)

                    # calculate other measures that have to do with sketch 
                    ls = [len(_y['svgData']) for _y in y]
                    svgStringLength.append(sum(ls))
                    y = coll.find({ '$and': [{'gameid': g}, {'eventType': 'stroke'}, {'trialNum': t['trialNum']}]}).sort('time')            
                    num_curves = [len([m.start() for m in re.finditer('c',str(_y['svgData']))]) for _y in y] ## gotcha: need to call string on _y['svgData'], o/w its unicode and re cant do anything with it
                    numCurvesPerSketch.append(sum(num_curves))
                    numCurvesPerStroke.append(sum(num_curves)/lastStrokeNum)
                    svgStringLengthPerStroke.append(sum(ls)/lastStrokeNum)
                    svgStringStd.append(np.std(ls))
                    timedOut.append(False)

                    ## calculate pixel intensity (amount of ink spilled) 

                    imsize = 100
                    numpix = imsize**2
                    thresh = 250
                    imgData = t['pngString']
                    filestr = base64.b64decode(imgData)
                    fname = os.path.join('sketch.png')
                    with open(fname, "wb") as fh:
                        fh.write(imgData.decode('base64'))
                    im = Image.open(fname).resize((imsize,imsize))
                    _im = np.array(im)
                    
                    meanPixelIntensity.append(len(np.where(_im[:,:,3].flatten()>thresh)[0])/numpix)
                    #print "trialNum: {}, meanPixelintensity: {}".format(t['trialNum'], len(np.where(_im[:,:,3].flatten()>thresh)[0])/numpix)

                ### aggregate game metadata
                TrialNum.append(t['trialNum'])
                GameID.append(t['gameid'])        
                Target.append(targetname)
                Category.append(category)
                Condition.append(t['condition'])
                Response.append(t['clickedName'])
                Outcome.append(t['correct'])
                Distractor1.append(distractors[0])
                Distractor2.append(distractors[1])
                Distractor3.append(distractors[2])  
                if (iterationName == 'run3_size4_waiting'):
                    Generalization.append('within')
                else:
                    Generalization.append('between')
                    
    
    ## now actually make dataframe
    GameID,TrialNum,Condition, Target, Category, Repetition, Phase, Generalization, drawDuration, Outcome, Response, numStrokes, meanPixelIntensity, svgStringLength, svgStringLengthPerStroke, svgStringStd, numCurvesPerSketch, numCurvesPerStroke, timedOut, png = map(np.array, \
    [GameID,TrialNum,Condition, Target, Category, Repetition, Phase, Generalization, drawDuration, Outcome, Response, numStrokes, meanPixelIntensity,svgStringLength, svgStringLengthPerStroke, svgStringStd, numCurvesPerSketch, numCurvesPerStroke, timedOut,png])    

    Repetition = map(int,Repetition)

    _D = pd.DataFrame([GameID,TrialNum,Condition, Target, Category, Repetition, Phase, Generalization, drawDuration, Outcome, Response, numStrokes, meanPixelIntensity,svgStringLength, svgStringLengthPerStroke, svgStringStd, numCurvesPerSketch, numCurvesPerStroke, timedOut, png], 
                     index = ['gameID','trialNum','condition', 'target', 'category', 'repetition', 'phase', 'Generalization', 'drawDuration', 'outcome', 'response', 'numStrokes', 'meanPixelIntensity', 'svgStringLength', 'svgStringLengthPerStroke', 'svgStringStd', 'numCurvesPerSketch', 'numCurvesPerStroke', 'timedOut', 'png'])
    _D = _D.transpose()

    # filter out crazy games (low accuracy and timeouts)
    accuracy_list = []
    timed_outs = []

    for g in _complete_games:
        D_ = _D[_D['gameID'] == g]
        all_accuracies = [d['outcome'] for i, d in D_.iterrows()]
        mean_accuracy = sum(all_accuracies) / float(len(all_accuracies))
        accuracy_list.append(mean_accuracy)
        if any(d['timedOut'] == True for i, d in D_.iterrows()):
            print ("timed out!")
            timed_outs.append(g)

    arr = np.array(accuracy_list)
    med = np.median(arr)
    sd = np.std(arr)
    crazy_games = [_complete_games[i] for i, acc in enumerate(accuracy_list) if (med-acc)/sd > 3]
    crazy_games = crazy_games + timed_outs
    if (len(crazy_games) > 0):
        print ("there were some crazy games: ", crazy_games)
    #complete_games= [item for item in _complete_games if item not in crazy_games]                 
    D = _D.loc[~_D['gameID'].isin(crazy_games)]

    # save out dataframe to be able to load in and analyze later w/o doing the above mongo querying ...
    D.to_csv(os.path.join(results_dir,'graphical_conventions_group_data_{}.csv'.format(iterationName)))

    #D_dining_repeated = D[(D['category'] == 'dining')& (D['condition'] == 'repeated')]
    # Just look at one game 

    return D

###############################################################################################

def filter_crazies(D, dv):
    arr = np.array(D[dv])
    keep = []
    for i, d in D.iterrows():
        if d[dv] < np.median(arr) + 3 * np.std(arr):
            keep.append(i)
    D_filtered = D.loc[keep]
    return D_filtered

###############################################################################################

### normalizing dataframe in terms of numstrokes
def grand_mean_normalize(D_normalized, dv, _complete_games):

    grand_mean = float(sum(list(D_normalized[dv])) / float(len(list(D_normalized[dv]))))
    for g in _complete_games:
        if g in list(D_normalized['gameID']):
            D_subject = D_normalized[D_normalized['gameID'] == g]
            subject_mean = float(sum(list(D_subject[dv])) / float(len(list(D_subject[dv]))))
            for i, d in D_normalized.iterrows():
                if d['gameID'] == g:
                    D_normalized.ix[i, dv] = float(d[dv]  - subject_mean + grand_mean)
                
    return D_normalized

###############################################################################################

def save_sketches(D, complete_games, sketch_dir, dir_name, iterationNum):
    for g in list(D['gameID']):
        print ("saving sketches from game: {}".format(g))
        if g in list(D['gameID']):
            _D = D[D['condition'] == 'repeated']
            for i,_d in _D.iterrows():
                imgData = _d['png']
                trialNum = _d['trialNum']
                target = _d['target']
                repetition = _d['repetition']
                filestr = base64.b64decode(imgData)
                fname = 'sketch.png'
                with open(fname, "wb") as fh:
                    fh.write(imgData.decode('base64'))
                im = Image.open(fname)
                #im = im.convert("RGB")
                ### saving sketches to sketch_dir 
                filepath = os.path.join('{}_{}_{}_{}_{}.png'.format(g,trialNum,target, repetition, iterationNum))     
                if not os.path.exists(os.path.join(sketch_dir,dir_name)):
                    os.makedirs(os.path.join(sketch_dir,dir_name))
                im.save(os.path.join(sketch_dir,dir_name,filepath))
                
###############################################################################################

def clean_up_metadata(M):
    M = M.rename(columns={'label':'path'})    
    label = [i.split('/')[-1] for i in M.path.values]    
    M = M.assign(label=pd.Series(label))
    M = M.drop(columns=['Unnamed: 0'])
    return M

###############################################################################################

def split_up_metadata(M):
    ## parse labels into columns for M
    new_M = pd.DataFrame(
        M.label.str.split('_',5).tolist(),
        columns = ['gameID','trialNum', 'category', 'targetID', 'repetition', 'iterationName']
    )
    new_M['objID'] = new_M.category.str.cat(new_M.targetID, sep = '_')
    new_M['feature_ind'] = pd.Series(range(len(new_M)))
    new_M['repetition'] = pd.to_numeric(new_M['repetition'])
    return new_M.drop(columns = ['category', 'targetID'])

###############################################################################################

# create and plot RDM 
def get_and_plot_RDM(M,F,sorted_feature_ind, axs, x_ind, y_ind, rep):
    ordered_objs = M['target'].unique()
    labels = M.target.values
    means = F
    ordered_means = means[sorted_feature_ind,:]
    sns.set_style('white')
    CORRMAT = np.corrcoef(ordered_means)
    sns.set_context('paper')
    ax = axs[y_ind, x_ind]
    ax.set_title("rep {}".format(rep), fontsize=30)
    sns.heatmap(1-CORRMAT, vmin=0, vmax=2, cmap="plasma", ax=ax, cbar=False, xticklabels=False, yticklabels=False)
    RDM = CORRMAT
    plt.tight_layout()    
    return RDM

###############################################################################################

def plot_accuracy_reps(D):
    mean_accuracy_list = []
    for i in range(0,8):
        outcome_list = (D.loc[D['repetition'] == i])['outcome']
        mean_accuracy = sum(outcome_list) / float(len(outcome_list))
        mean_accuracy_list.append(mean_accuracy)
    D_mean = pd.DataFrame()
    D_mean['meanAccuracy'] = mean_accuracy_list
    D_mean['repetition'] = range(0,8)
    D_mean
    plt.figure(figsize=(6,6))
    sns.regplot(data=D_mean,
             x='repetition',
             y='meanAccuracy',
             ci = None)    
    plt.ylim([0.5,1.0])
    plt.xticks(np.arange(0, 8, step=1))
    
###############################################################################################

def plot_accuracy_phase(D):
    for i, o in enumerate(D['outcome']):
        if o == True:
            D.set_value(i, 'outcome', 1)
        else:
            D.set_value(i, 'outcome', 0)
    D['outcome'] = D['outcome'].astype(int)

    _D1 = D[D['phase']!='repeated'] ## exclude "repetition-phase" trials
    D1 = _D1.groupby(['gameID','phase','condition'])['outcome'].mean()
    D1 = D1.reset_index()    

    plt.figure(figsize=(6,6))
    sns.pointplot(data=D1,
             x='phase',
             y='outcome',
             hue='condition',
             order=['pre','post'])    
    plt.ylim([0.6,1.0])

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
    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(nrows=2, ncols=2, figsize=(12,12))

    plot_repeated_control(D0_repeated, D0_control, var0, ax0, numReps)
    plot_repeated_control(D1_repeated, D1_control, var1, ax1, numReps)
    plot_repeated_control(D2_repeated, D2_control, var2, ax2, numReps)
    plot_repeated_control(D3_repeated, D3_control, var3, ax3, numReps)

    ax0.set_ylim([4, 8])
    ax0.set(xlim=(-0.5, numReps - 0.5), xticks=range(0,8))
    ax1.set_ylim([5, 15])
    ax1.set(xlim=(-0.5, numReps - 0.5), xticks=range(0,8))
    ax2.set_ylim([15, 25])
    ax2.set(xlim=(-0.5, numReps - 0.5), xticks=range(0,8))
    ax3.set_ylim([0.02, 0.045])
    ax3.set(xlim=(-0.5, numReps - 0.5), xticks=range(0,8))
    
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
             dodge=True,
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
        print ('Printing out sketches from game: ' + g)
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

    for g in complete_games:
        print ('Printing out sketches from game: ' + g)
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
        print ('Printing out sketches from game: ' + g)
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
        print ('Printing out sketches from game: ' + g)
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
    
    
###############################################################################################   

def plot_between_interaction_similarity(M):
    ### computing average of upper triangle of RDM and plotting across repetitions 
    new_df = pd.DataFrame()
    for targ in M['target'].unique():
        M_targ = M[M['target'] == targ]
        M_targ.sort_values(by=['repetition'])
        for rep in range(8):
            M_targ_rep = M_targ[M_targ['repetition'] == str(int(rep))]
            inds_to_compare = M_targ_rep['feature_ind']
            features_to_compare = F[inds_to_compare, :]
            CORRMAT = np.corrcoef(features_to_compare)
            avr = np.mean(np.tril(CORRMAT)) # only upper triangle 
            df_to_add = pd.DataFrame([[rep, targ, avr]], columns=['repetition', 'target', 'average_similarity'])
            new_df = new_df.append(df_to_add)
    sns.set_context('paper')
    plt.figure(figsize=(8,5))
    sns.lineplot(data=new_df, x='repetition', y='average_similarity', estimator = np.mean)
    plt.xlim(-0.5, 7.5)
    
############################################################################################### 
    
def scramble_df_within_target_rep(M):
    M_pseudo = pd.DataFrame()
    for target in M['target'].unique():
        M_targ = M[M['target'] == target]
        for rep in M_targ['repetition'].unique():
            M_targ_rep = M_targ[M_targ['repetition'] == rep]
            gameIDs = np.array(M_targ_rep['gameID'])
            np.random.shuffle(gameIDs)
            M_targ_rep['pseudo_gameID'] = list(gameIDs)
            M_pseudo = M_pseudo.append(M_targ_rep)
    return M_pseudo

############################################################################################### 
    
def make_adjacency_matrix(M, F, gameID):
    print(F)
    result = np.zeros((8, 8))
    count = 0
    F_ = np.vstack((F, [float('NaN')] * 4096))
    arr_of_corrmats = []
    for game in M.gameID.unique(): #['3480-03933bf3-5e7e-4ecd-b151-7ae57e6ae826']:
        for target in M.query('gameID == "{}"'.format(game)).objID.unique():  #['dining_04']:
            count = count + 1
            M_isolated = M.query('gameID == "{}" and objID == "{}"'.format(game, target))
            for rep in range(8):
                if rep not in list(M_isolated['repetition']):
                    df_to_add = pd.DataFrame([[game, float('NaN'), rep, target, len(F)]], 
                                             columns=[gameID, 'trialNum', 'repetition', 'objID', 'feature_ind'])
                    M_isolated = M_isolated.append(df_to_add)
            M_isolated_sorted = M_isolated.sort_values(by=['repetition'])
            inds_to_compare = M_isolated_sorted['feature_ind']
            features_to_compare = F_[inds_to_compare, :]
            print(inds_to_compare.shape)
            print(features_to_compare)
            # add features to a new dataframe 
            # and compute corr with pandas to handle NaN well  
            features_df = pd.DataFrame()
            column_index = 0
            for row in features_to_compare:
                features_df[str(column_index)] = pd.Series(list(row))
                column_index = column_index + 1
            print(features_df)
            pd_CORRMAT = features_df.corr()
            print(pd_CORRMAT)
            np_CORRMAT = pd_CORRMAT.values
            arr_of_corrmats.append(np_CORRMAT)

    for i in range(8):
        for j in range(8):
            to_add = [mat[i][j] for mat in arr_of_corrmats]
            result[i][j] = np.nanmean(np.array(to_add))

    average_corr_mat = np.array(result)
    
    sns.set_context('paper')
    fig, ax = plt.subplots(figsize=(5,4)) 
    sns.heatmap(1-average_corr_mat, cmap="plasma", cbar=True, xticklabels=True, yticklabels=True, ax=ax)
    plt.tight_layout()   
    
    return arr_of_corrmats
    
############################################################################################### 

def plot_within_interaction_similarity(arr_of_corrmats):
    one_back_df = pd.DataFrame()
    for base_rep in range(7):
        for i, corrmat in enumerate(arr_of_corrmats):
            corrcoef = corrmat[base_rep][base_rep+1]
            df_to_add = pd.DataFrame([[i, base_rep, corrcoef]], columns=['corrmat_num','base_rep', 'similarity']) 
            one_back_df = one_back_df.append(df_to_add)
    sns.lineplot(
        data=one_back_df, 
        estimator=np.mean,
        x='base_rep',
        y='similarity')
    
############################################################################################### 
    
def standardize(D, dv):
    new_D = pd.DataFrame()
    trialNum_list = []
    dv_list = []
    rep_list = []
    for g in list(D['gameID']):
        D_game = D[D['gameID'] == g]
        mean = np.mean(np.array(D_game[dv]))
        std = np.std(np.array(D_game[dv]))
        for t in list(D_game['trialNum']):
            D_trial = D_game[D_game['trialNum'] == t]
            trialNum_list.append(t)
            z_score = (list(D_trial[dv])[0] - mean) / std
            dv_list.append(z_score)
            rep_list.append(list(D_trial['repetition'])[0])
    new_D['trialNum'] = trialNum_list
    new_D[dv] = dv_list
    new_D['repetition'] = rep_list
    return new_D

############################################################################################### 

def add_bis_scores(D, dv):
    new_D = D.copy(deep=True)
    bis_score_list = []
    for i,d in D.iterrows():
        bis_score = d['outcome'] - d[dv] 
        bis_score_list.append(bis_score)
    new_D['bis_score'] = bis_score_list
    return new_D
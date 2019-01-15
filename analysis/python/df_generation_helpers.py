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
from IPython.display import clear_output

sns.set_context('poster')
colors = sns.color_palette("cubehelix", 5)

################################################################################################
# Dictionaries to convert between objects and categories

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
# map object names to shapenet ids 

object_to_shapenet = {
    "dining_00":"30afd2ef2ed30238aa3d0a2f00b54836",
    "dining_01":"30dc9d9cfbc01e19950c1f85d919ebc2",
    "dining_02":"4c1777173111f2e380a88936375f2ef4",
    "dining_03":"3466b6ecd040e252c215f685ba622927",
    "dining_04":"38f87e02e850d3bd1d5ccc40b510e4bd",
    "dining_05":"3cf6db91f872d26c222659d33fd79709",
    "dining_06":"3d7ebe5de86294b3f6bcd046624c43c9",
    "dining_07":"56262eebe592b085d319c38340319ae4",
    "waiting_00":"1d1641362ad5a34ac3bd24f986301745",
    "waiting_01":"1da9942b2ab7082b2ba1fdc12ecb5c9e",
    "waiting_02":"2448d9aeda5bb9b0f4b6538438a0b930",
    "waiting_03":"23b0da45f23e5fb4f4b6538438a0b930",
    "waiting_04":"2b5953c986dd08f2f91663a74ccd2338",
    "waiting_05":"2e291f35746e94fa62762c7262e78952",
    "waiting_06":"2eaab78d6e4c4f2d7b0c85d2effc7e09",
    "waiting_07":"309674bdec2d24d7597976c675750537"
}

################################################################################################
# helper functions to generate dataframe

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
        #clear_output(wait=True)
        print('{} | {}'.format(i,game))
        clear_output(wait=True)
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

    # new field in run5_submitButton to keep track of which subset of dining/waiting chairs used
    if iterationName == 'run5_submitButton':
        Subset = []
    
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
    svgString = [] # svg string representation of ksetch
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

            # collection of all clickedObj events in a particular game
            X = coll.find({ '$and': [{'gameid': g}, {'eventType': 'clickedObj'}]}).sort('time')
            # collection of all stroke events in a particular game
            Y = coll.find({ '$and': [{'gameid': g}, {'eventType': 'stroke'}]}).sort('time')
            counter = 0
            for t in X: # for each clickedObj event
                print( 'Analyzing game {} | {} of {} | trial {}'.format(g, i, len(_complete_games),counter))
                clear_output(wait=True)                                
                counter += 1
                targetname = t['intendedName']
                category = OBJECT_TO_CATEGORY_run2[targetname]
                Phase.append(t['phase'])
                Repetition.append(t['repetition'])
                distractors = [t['object2Name'],t['object3Name'],t['object4Name']]
                full_list = [t['intendedName'],t['object2Name'],t['object3Name'],t['object4Name']]
                png.append(t['pngString'])
                if iterationName == 'run5_submitButton':
                    Subset.append(t['subset'])

                #for each stroke event with same trial number as this particular clickedObj event
                y = coll.find({ '$and': [{'gameid': g}, {'eventType': 'stroke'}, {'trialNum': t['trialNum']}]}).sort('time')
                # have to account for cases in which sketchers do not draw anything
                if (y.count() == 0):
                    numStrokes.append(float('NaN'))
                    drawDuration.append(float('NaN'))
                    svgString.append('NaN')
                    numCurvesPerSketch.append(float('NaN'))
                    numCurvesPerStroke.append(float('NaN'))
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

                    # extract svg string into list
                    svg_list = [_y['svgData'] for _y in y]

                    # calculate other measures that have to do with sketch
                    y = coll.find({ '$and': [{'gameid': g}, {'eventType': 'stroke'}, {'trialNum': t['trialNum']}]}).sort('time')
                    num_curves = [len([m.start() for m in re.finditer('c',str(_y['svgData']))]) for _y in y] ## gotcha: need to call string on _y['svgData'], o/w its unicode and re cant do anything with it
                    numCurvesPerSketch.append(sum(num_curves))
                    numCurvesPerStroke.append(sum(num_curves)/lastStrokeNum)
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
                svgString.append(svg_list)
                if (iterationName == 'run3_size4_waiting'):
                    Generalization.append('within')
                else:
                    Generalization.append('between')


    ## now actually make dataframe
    GameID,TrialNum,Condition, Target, Category, Repetition, Phase, Generalization, drawDuration, Outcome, Response, numStrokes, meanPixelIntensity, numCurvesPerSketch, numCurvesPerStroke, timedOut, png,svgString = map(np.array, \
    [GameID,TrialNum,Condition, Target, Category, Repetition, Phase, Generalization, drawDuration, Outcome, Response, numStrokes, meanPixelIntensity, numCurvesPerSketch, numCurvesPerStroke, timedOut,png, svgString])

    Repetition = map(int,Repetition)

    _D = pd.DataFrame([GameID,TrialNum,Condition, Target, Category, Repetition, Phase, Generalization, drawDuration, Outcome, Response, numStrokes, meanPixelIntensity, numCurvesPerSketch, numCurvesPerStroke, timedOut, png,svgString],
                     index = ['gameID','trialNum','condition', 'target', 'category', 'repetition', 'phase', 'Generalization', 'drawDuration', 'outcome', 'response', 'numStrokes', 'meanPixelIntensity', 'numCurvesPerSketch', 'numCurvesPerStroke', 'timedOut', 'png','svgString'])
    _D = _D.transpose()
    
    # if run5_submitButton, add the subset column
    if iterationName == 'run5_submitButton':
        _D = _D.assign(subset=pd.Series(Subset))

    # filter out crazy games (low accuracy and timeouts)
    accuracy_list = []
    timed_outs = []

    for g in _complete_games:
        D_ = _D[_D['gameID'] == g]
        all_accuracies = [d['outcome'] for i, d in D_.iterrows()]
        mean_accuracy = sum(all_accuracies) / float(len(all_accuracies))
        accuracy_list.append(mean_accuracy)
        if any(d['timedOut'] == True for i, d in D_.iterrows()):
            print ("Game: {} timed out!".format(g))
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
    print 'Done!'
    return D

###############################################################################################

def find_crazies(D):
    arr1 = np.array(D['numStrokes'])
    arr2 = np.array(D['numCurvesPerSketch'])
    crazies = []
    for i, d in D.iterrows():
        if d['numStrokes'] < np.median(arr1) + 3 * np.std(arr1) and d['numCurvesPerSketch'] < np.median(arr2) + 3 * np.std(arr2):
            crazies.append(False)
        else:
            crazies.append(True)
    D['crazy'] = crazies
    return D

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

def save_sketches(D, sketch_dir, dir_name, iterationName):
    for i,_d in D.iterrows():
        print ("saving trial {} sketch from game: {}".format(_d['trialNum'],_d['gameID']))
        clear_output(wait=True)
        g = _d['gameID']
        cond = _d['condition']
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
        filepath = os.path.join('{}_{}_{}_{}_{}_{}.png'.format(iterationName, g, trialNum, cond, target, repetition))
        if not os.path.exists(os.path.join(sketch_dir,dir_name)):
            os.makedirs(os.path.join(sketch_dir,dir_name))
        im.save(os.path.join(sketch_dir,dir_name,filepath))

###############################################################################################

def zscore(x,mu,sd):
    return (x-mu)/(sd+1e-6)

def standardize(D, dv):
    new_D = pd.DataFrame()
    trial_list = []
    dv_list = []
    rep_list = []
    game_id_list = []
    target_list = []
    condition_list = []
    generalization_list = []
    
    grouped = D.groupby('gameID')  
    ## loop through games
    for gamename, group in grouped:
        mu = np.mean(np.array(group[dv]))
        sd = np.std(np.array(group[dv]))        
        ## loop through trials within games        
        trialwise = group.groupby('trialNum')
        for trialname,trial in trialwise:            
            trial_list.append(trialname)
            val = trial[dv].values[0]
            z_score = zscore(val, mu, sd)             
            dv_list.append(z_score)
            rep_list.append(trial['repetition'].values[0])       
            game_id_list.append(gamename)                           
            target_list.append(trial['target'].values[0])
            condition_list.append(trial['condition'].values[0])
            generalization_list.append(trial['generalization'].values[0])
            
    new_D['trialNum'] = trial_list
    new_D[dv] = dv_list
    new_D['repetition'] = rep_list
    new_D['gameID'] = game_id_list
    new_D['target'] = target_list
    new_D['condition'] = condition_list    
    new_D['generalization'] = generalization_list
    
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

###############################################################################################

def save_bis_scores(D, results_dir):

    # split into repeated and control
    D_repeated = D[D['condition'] == 'repeated']
    D_control = D[D['condition'] == 'control']
    D_control.repetition = D_control.repetition.replace(1, 7)
    D = pd.concat([D_repeated, D_control], axis = 0)

    standardized_outcome = standardize(D, 'outcome')
    standardized_outcome = standardized_outcome.loc[:,'outcome']
    standardized_drawDuration = standardize(D, 'drawDuration')
    standardized_numStrokes = standardize(D, 'numStrokes')

    drawDuration_accuracy = pd.concat([standardized_drawDuration, standardized_outcome], axis = 1)
    numStrokes_accuracy = pd.concat([standardized_numStrokes, standardized_outcome], axis = 1)

    drawDuration_accuracy_bis = add_bis_scores(drawDuration_accuracy, 'drawDuration')
    numStrokes_accuracy_bis = add_bis_scores(numStrokes_accuracy, 'numStrokes')

    drawDuration_accuracy_bis.to_csv(os.path.join(results_dir, "graphical_conventions_{}_{}.csv".format('bis_score', 'drawDuration')))
    numStrokes_accuracy_bis.to_csv(os.path.join(results_dir, "graphical_conventions_{}_{}.csv".format('bis_score', 'numStrokes')))

    return drawDuration_accuracy_bis, numStrokes_accuracy_bis


###############################################################################################

def add_recog_session_ids(D):

    D_repeated = D[D['condition'] == 'repeated']
    D_control = D[D['condition'] == 'control']

    repeated_tuple_list = []
    for g in D_repeated['gameID'].unique():
        target_list = D_repeated[D_repeated['gameID'] == g]['target'].unique()
        for t in target_list:
            repeated_tuple_list.append((g, t))
    repeated = np.array(repeated_tuple_list)

    control_tuple_list = []
    for g in D_control['gameID'].unique():
        target_list = D_control[D_control['gameID'] == g]['target'].unique()
        for t in target_list:
            control_tuple_list.append((g, t))
    control = np.array(control_tuple_list)

    assert len(repeated) == 268
    assert len(control) == 268

    new_d = pd.DataFrame()
    for rep in range(8):
        new_d['repeated_rep_{}'.format(rep)] = list(np.roll(repeated, rep * 4, axis=0))

    for rep in [0,7]:
        new_d['control_rep_{}'.format(rep)] = list(np.roll(control, (rep+8) * 4, axis=0))

    D['recog_id'] = [0] * len(D)

    for i,d in new_d.iterrows():
        for j, pair in enumerate(list(d)):
            if j == 8 or j == 9:
                condition = 'control'
                rep_num = 0 if j == 8 else 1
            else:
                condition = 'repeated'
                rep_num = j
            row_index = list(D.index[(D['gameID'] == pair[0]) & (D['target'] == pair[1]) & (D['repetition'] == rep_num) & (D['condition'] == condition)])[0]
            D.loc[row_index, 'recog_id'] = i

    return D

###############################################################################################

# add target shapenet ids
def add_distractors_and_shapenet_ids(D):
    target_shapenets = [0] * len(D)
    D['target_shapenet'] = target_shapenets
    for i,d in D.iterrows():
        target = d['target']
        shapenet_id = object_to_shapenet[target]
        D.loc[i, 'target_shapenet'] = shapenet_id
    # add distractor
    # add shapenet ids for distractors
    distractors = [[0]] * len(D)
    distractors_shapenets = [[0]] * len(D)
    D['distractors'] = distractors
    D['distractors_shapenet'] = distractors_shapenets
    for i,d in D.iterrows():
        gameID = d['gameID']
        condition = d['condition']
        target_list = D[(D['gameID'] == gameID) & (D['condition'] == condition)]['target'].unique()
        distractors_list = [target for target in target_list if target !=  d['target']]
        distractors_dict = {'distractor1':distractors_list[0],'distractor2':distractors_list[1],'distractor3':distractors_list[2]}
        D.at[i, 'distractors'] = distractors_dict
        shapenets_list = [object_to_shapenet[dist] for dist in distractors_list]
        shapenets_dict = {'distractor1':shapenets_list[0],'distractor2':shapenets_list[1],'distractor3':shapenets_list[2]}
        D.at[i, 'distractors_shapenet'] = shapenets_dict
    if 'Unnamed: 0' in list(D.columns.values):
        D = D.drop(['Unnamed: 0'], axis=1)
    if 'row_index' in list(D.columns.values):
        D = D.drop(['row_index'], axis=1)
    return D

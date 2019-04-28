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
from matplotlib import colors
import seaborn as sns
import re
sns.set_context('poster')
colors = sns.color_palette("cubehelix", 5)
from svgpathtools import parse_path, wsvg, svg2paths

# directory & file hierarchy
proj_dir = os.path.abspath('../../..')
analysis_dir = os.getcwd()
results_dir = os.path.join(proj_dir,'results')

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

def clean_up_metadata(M):
    return (M.assign(feature_ind=pd.Series(range(len(M))))
             .assign(repetition=pd.to_numeric(M.repetition)))
             #drop(columns=['Unnamed: 0'])

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

def plot_between_interaction_similarity(M, F, rep_name):
    ### computing average of upper triangle of RDM and plotting across repetitions
    new_df = pd.DataFrame()
    for targ in sorted(M['target'].unique()):
        M_targ = M[M['target'] == targ]
        M_targ.sort_values(by=[rep_name])
        for rep in range(8):
            M_targ_rep = M_targ[M_targ[rep_name] == int(rep)]
            inds_to_compare = M_targ_rep['feature_ind']
            features_to_compare = F[inds_to_compare, :]
            CORRMAT = np.corrcoef(features_to_compare)
            avr = np.mean(np.ma.masked_equal(np.tril(CORRMAT, -1), 0)) # only upper triangle
            df_to_add = pd.DataFrame([[rep, targ, avr]], columns=[rep_name, 'target', 'average_similarity'])
            new_df = new_df.append(df_to_add)
    sns.set_context('paper')
    plt.figure(figsize=(8,5))
    sns.lineplot(data=new_df, x=rep_name, y='average_similarity', estimator = np.mean)
    plt.xlim(-0.5, 7.5)

###############################################################################################

def scramble_df_across_gameID_within_target_and_rep(M):
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

def scramble_df_across_repetition_within_target_and_gameID(M):
    M_pseudo = pd.DataFrame()
    for target in M['target'].unique():
        M_targ = M[M['target'] == target]
        for gameID in M_targ['gameID'].unique():
            M_targ_game = M_targ[M_targ['gameID'] == gameID]
            repetitions = np.array(M_targ_game['repetition'])
            np.random.shuffle(repetitions)
            M_targ_game['pseudo_repetition'] = list(repetitions)
            M_pseudo = M_pseudo.append(M_targ_game)
    return M_pseudo

###############################################################################################

def make_adjacency_matrix(M, F, gameID_colname):
    # add scratch index to handle NaNs
    F_ = np.vstack((F, [float('NaN')] * 4096))
    arr_of_corrmats = []
    for game in sorted(M[gameID_colname].unique()): #['3480-03933bf3-5e7e-4ecd-b151-7ae57e6ae826']:
        for target in sorted(M.query('{} == "{}"'.format(gameID_colname, game)).target.unique()):  #['dining_04']:
            M_instance = M.query('{} == "{}" and target == "{}"'.format(gameID_colname, game, target))
            for rep in range(8):
                if rep not in list(M_instance['repetition']):
                    df_to_add = pd.DataFrame([[game, float('NaN'), rep, target, len(F)]],
                                             columns=[gameID_colname, 'trialNum', 'repetition', 'target', 'feature_ind'])
                    M_instance = M_instance.append(df_to_add)
            M_instance_sorted = M_instance.sort_values(by=['repetition'])
            inds_to_compare = M_instance_sorted['feature_ind']
            features_to_compare = F_[inds_to_compare, :]
            # transpose array so that features are columns
            # pandas .corr() handles NaNs better and expects columns
            pd_CORRMAT = pd.DataFrame(features_to_compare.T).corr()
            arr_of_corrmats.append(pd_CORRMAT.values)

    # Average across games and targets for each entry in matrix
    result = np.zeros((8, 8))
    for i in range(8):
        for j in range(8):
            to_add = [mat[i][j] for mat in arr_of_corrmats]
            result[i][j] = np.nanmean(np.array(to_add))

    average_corr_mat = np.array(result)
    print(average_corr_mat)
    # Plot it
    sns.set_context('paper')
    fig, ax = plt.subplots(figsize=(5,4))
    sns.heatmap(1-average_corr_mat, cmap="plasma", cbar=True, ax=ax)
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
    game_id_list = []
    target_list = []
    condition_list = []
    for g in D['gameID'].unique():
        D_game = D[D['gameID'] == g]
        mean = np.mean(np.array(D_game[dv]))
        std = np.std(np.array(D_game[dv]))
        for t in list(D_game['trialNum']):
            game_id_list.append(g)
            D_trial = D_game[D_game['trialNum'] == t]
            trialNum_list.append(t)
            if std == 0:
                z_score = 0
            else:
                z_score = (list(D_trial[dv])[0] - mean) / float(std)
            dv_list.append(z_score)
            rep_list.append(list(D_trial['repetition'])[0])
            condition_list.append(list(D_trial['condition'])[0])
            target_list.append(list(D_trial['target'])[0])
    new_D['trialNum'] = trialNum_list
    new_D[dv] = dv_list
    new_D['repetition'] = rep_list
    new_D['gameID'] = game_id_list
    new_D['condition'] = condition_list
    new_D['target'] = target_list
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

def save_bis_scores(D):

    # split into repeated and control
    D_repeated = D[D['condition'] == 'repeated']
    D_control = D[D['condition'] == 'control']
    D_control.repetition = D_control.repetition.replace(1, 7)
    D = pd.concat([D_repeated, D_control], axis = 0)

    standardized_outcome = standardize(D, 'outcome')
    standardized_outcome = standardized_outcome.drop(['repetition', 'trialNum', 'gameID','condition', 'target'], axis = 1)
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

def compute_similarity(F, inds_to_compare): # inds_to_compare: feature indices
    features_to_compare = F[inds_to_compare, :]
    CORRMAT = np.corrcoef(features_to_compare)
    similarity = np.mean(np.ma.masked_equal(np.tril(CORRMAT, -1), 0))
    #np.mean(np.ma.masked_equal(np.tril(CORRMAT, -1), 0))#(np.tril(CORRMAT)) # (np.ma.masked_equal(np.tril(CORRMAT, -1), 0))
    return similarity

###############################################################################################

def plot_stroke_similarity_rep_specific(d, lesion_later_sketch, axs):
    for base_rep in range(7):
        for direction in ['start', 'end']:
            ax=axs[base_rep]
            next_rep = base_rep + 1
            d_ = d[(d['base_rep'] == base_rep) & (d['direction'] == direction) & (d['lesion_later_sketch'] == lesion_later_sketch)]
            color = 'lightcoral' if direction == 'start' else 'turquoise'
            intact = base_rep if lesion_later_sketch else next_rep
            lesioned = next_rep if lesion_later_sketch else base_rep
            a = sns.regplot(x="percentage_strokes_deleted", y='similarity', data=d_, x_bins=10, ax=ax, color=color)
            a.set_title('Comparing intact repetition {} and repetition {} with stroke deletions'.format(intact, lesioned))
            a.set_ylabel('Normalized similarity')
            a.set_xlabel('Percentage of strokes deleted')

###############################################################################################

def plot_stroke_similarity_rep_aggregate(d, lesion_later_sketch, ax):
    for direction in ['start', 'end']:
        d_ = d[(d['direction'] == direction) & (d['lesion_later_sketch'] == lesion_later_sketch)]
        color = 'lightcoral' if direction == 'start' else 'turquoise'
        label = 'delete from start' if direction == 'start' else 'delete from end'
        a = sns.regplot(x="percentage_strokes_deleted", y='similarity', data=d_, x_bins=10, ax=ax, color=color, label=label)
        later_or_earlier = "later" if lesion_later_sketch else "earlier"
        a.set_title('Similarity timecourse between adjacent repetitions with stroke deletion of {} sketch'.format(later_or_earlier))
        a.set_ylabel('Normalized similarity')
        a.set_xlabel('Percentage of strokes deleted')
        a.legend()

###############################################################################################

def plot_stroke_similarity_discrete(d, lesion_later_sketch):
    num_graphs = len(d['total_num_strokes'].unique())
    fig, axs = plt.subplots(nrows=num_graphs, figsize=(5,100))
    count = 0
    total_num_strokes_list = list(set(d['total_num_strokes']))
    total_num_strokes_list.sort()
    for total_num_strokes in total_num_strokes_list:
        _d = d[d['total_num_strokes'] == total_num_strokes]
        ax=axs[count]
        count += 1
        for direction in ['start', 'end']:
            d_ = _d[(_d['direction'] == direction) & (_d['lesion_later_sketch'] == lesion_later_sketch)]
            color = 'lightcoral' if direction == 'start' else 'turquoise'
            label = 'delete from start' if direction == 'start' else 'delete from end'
            a = sns.regplot(x="num_strokes_deleted", y='similarity', data=d_, ax=ax, color=color, label=label, scatter_kws={'s':2}, x_estimator=np.mean)
            later_or_earlier = "later" if lesion_later_sketch else "earlier"
            a.set_title('Similarity timecourse between adjacent repetitions with stroke deletion of {} sketch (total number of strokes: {})'.format(later_or_earlier, str(total_num_strokes)))
            a.set_ylabel('Normalized similarity')
            a.set_xlabel('Number of strokes deleted')
            a.legend()

###############################################################################################
def compute_similarity_2(F1, F2, inds_to_compare): # inds_to_compare: feature indices
    features_to_compare = [F1[inds_to_compare[0]], F2[inds_to_compare[1]]]
    CORRMAT = np.corrcoef(features_to_compare)
    similarity = np.mean(np.ma.masked_equal(np.tril(CORRMAT, -1), 0))
    #np.mean(np.ma.masked_equal(np.tril(CORRMAT, -1), 0))#(np.tril(CORRMAT)) # (np.ma.masked_equal(np.tril(CORRMAT, -1), 0))
    return similarity


def get_stroke_analysis_df(D, M, F):
    d = pd.DataFrame()
    for direction in ['start', 'end']:
        for lesion_later_sketch in [True, False]:
            for base_rep in range(7):
                next_rep = base_rep + 1
                # make dataframe with gameid, target, percentage strokes deleted, and similarity
                for g in M['gameID'].unique():
                    # retrieve repeated condition targets from game
                    repeated_targets = D[(D['gameID'] == g) & (D['condition'] == 'repeated')]['target'].unique()
                    repeated_targets_ = [target.split('_')[0] + target.split('_')[1] for target in repeated_targets]
                    assert len(repeated_targets_) == 4
                    for t in repeated_targets_:
                        if lesion_later_sketch:
                            # get feature inds of each stroke-deletion version of later sketch
                            all_strokes_to_delete = M[(M['gameID'] == g) & (M['target'] == t) & (M['repetition'] == next_rep) & (M['direction'] == direction)]
                            # get feature ind of intact earlier sketch
                            feature_ind_of_paired_sketch = M[(M['gameID'] == g) & (M['target'] == t) & (M['repetition'] == base_rep) & (M['num_strokes_deleted'] == 0) & (M['direction'] == direction)]['feature_ind'].unique()[0]
                        else:
                            # get feature inds of each stroke-deletion version of earlier sketch
                            all_strokes_to_delete = M[(M['gameID'] == g) & (M['target'] == t) & (M['repetition'] == base_rep) & (M['direction'] == direction)]
                            # get feature ind of intact later sketch
                            feature_ind_of_paired_sketch = M[(M['gameID'] == g) & (M['target'] == t) & (M['repetition'] == next_rep) & (M['num_strokes_deleted'] == 0) & (M['direction'] == direction)]['feature_ind'].unique()[0]
                        total_num_strokes = len(all_strokes_to_delete)
                        for num_deleted in range(len(all_strokes_to_delete)):
                            # for each stroke deletion step of the lesioned sketch, compute percentage of strokes deleted and similarity between that version and the intact version of the adjacent repetition
                            percentage_deleted = float(num_deleted) / float(total_num_strokes)
                            feature_ind_of_deleted_sketch = all_strokes_to_delete[(all_strokes_to_delete['num_strokes_deleted'] == num_deleted) & (all_strokes_to_delete['direction'] == direction)]['feature_ind'].unique()[0]
                            similarity = compute_similarity(F, [feature_ind_of_paired_sketch, feature_ind_of_deleted_sketch])
                            if num_deleted == 0:
                                baseline_similarity = similarity
                            normalized_similarity = float(similarity) / float(baseline_similarity)
                            df_to_add = pd.DataFrame([[g, t, percentage_deleted, num_deleted, total_num_strokes, normalized_similarity, base_rep, direction, lesion_later_sketch]], columns=['gameID', 'target', 'percentage_strokes_deleted', 'num_strokes_deleted', 'total_num_strokes', 'similarity', 'base_rep', 'direction', 'lesion_later_sketch'])
                            d = d.append(df_to_add)
    return d


###############################################################################################
def get_self_similarity_df(D, M, F):
    d = pd.DataFrame()
    for direction in ['start', 'end']:
        for rep in range(7):
            # make dataframe with gameid, target, percentage strokes deleted, and similarity
            for g in M['gameID'].unique():
                # retrieve repeated condition targets from game
                repeated_targets = D[(D['gameID'] == g) & (D['condition'] == 'repeated')]['target'].unique()
                repeated_targets_ = [target.split('_')[0] + target.split('_')[1] for target in repeated_targets]
                assert len(repeated_targets_) == 4
                for t in repeated_targets_:
                    # get feature inds of each stroke-deletion version of later sketch
                    all_strokes_to_delete = M[(M['gameID'] == g) & (M['target'] == t) & (M['repetition'] == rep) & (M['direction'] == direction)]
                    # get feature ind of intact earlier sketch
                    feature_ind_of_paired_sketch = M[(M['gameID'] == g) & (M['target'] == t) & (M['repetition'] == rep) & (M['num_strokes_deleted'] == 0) & (M['direction'] == direction)]['feature_ind'].unique()[0]
                    total_num_strokes = len(all_strokes_to_delete)
                    for num_deleted in range(len(all_strokes_to_delete)):
                        # for each stroke deletion step of the lesioned sketch, compute percentage of strokes deleted and similarity between that version and the intact version of the adjacent repetition
                        percentage_deleted = float(num_deleted) / float(total_num_strokes)
                        feature_ind_of_deleted_sketch = all_strokes_to_delete[(all_strokes_to_delete['num_strokes_deleted'] == num_deleted) & (all_strokes_to_delete['direction'] == direction)]['feature_ind'].unique()[0]
                        similarity = compute_similarity(F, [feature_ind_of_paired_sketch, feature_ind_of_deleted_sketch])
                        #if num_deleted == 0:
                        #    baseline_similarity = similarity
                        #normalized_similarity = float(similarity) / float(baseline_similarity)
                        df_to_add = pd.DataFrame([[g, t, percentage_deleted, num_deleted, total_num_strokes, similarity, rep, direction]], columns=['gameID', 'target', 'percentage_strokes_deleted', 'num_strokes_deleted', 'total_num_strokes', 'similarity', 'base_rep', 'direction'])
                        d = d.append(df_to_add)
    return d

###############################################################################################
def plot_self_similarity(d, axs):
    sns.set(style="ticks", rc={"lines.linewidth": 0.7})
    sns.set_context("paper")
    for base_rep in range(7):
        for direction in ['start', 'end']:
            ax=axs[base_rep]
            d_ = d[(d['base_rep'] == base_rep) & (d['direction'] == direction)]
            color = 'lightcoral' if direction == 'start' else 'turquoise'
            a = sns.regplot(x="percentage_strokes_deleted", y='similarity', data=d_, x_bins=10, ax=ax, color=color)
            a.set_title('Similarity to whole sketch with increasing stroke deletion in rep  {}'.format(str(base_rep)))
            a.set_ylabel('Similarity')
            a.set_xlabel('Percentage of strokes deleted')
            
###############################################################################################           
            
            
 # delete every stroke from whole sketch and plot similarity to whole sketch against length of stroke 
def get_one_deleted_df(D, M, F, Ms, Fs):
    d = pd.DataFrame()
    for rep in range(8):
        # make dataframe with gameid, target, percentage strokes deleted, and similarity
        for g in M['gameID'].unique():
            # retrieve repeated condition targets from game
            repeated_targets = D[(D['gameID'] == g) & (D['condition'] == 'repeated')]['target'].unique()
            #repeated_targets_ = [target.split('_')[0] + target.split('_')[1] for target in repeated_targets]
            assert len(repeated_targets) == 4
            for t in repeated_targets:
                # get feature inds of each stroke-deletion version of later sketch
                all_strokes_to_delete = M[(M['gameID'] == g) & (M['target'] == t) & (M['repetition'] == rep)]
                # get feature ind of intact earlier sketch
                t_ = t.split('_')[0] + t.split('_')[1]
                feature_ind_of_paired_sketch = Ms[(Ms['gameID'] == g) & (Ms['target'] == t_) & (Ms['repetition'] == rep) & (Ms['num_strokes_deleted'] == 0) & (Ms['direction'] == 'start')]['feature_ind'].unique()[0]
                total_num_strokes = len(all_strokes_to_delete)
                D_ = D[(D['gameID'] == g) & (D['target'] == t) & (D['repetition'] == rep)]
                svgListString = list(D_['svgString'])[0]
                arcLengths = getArcLengths(svgListString)
                for num_deleted in range(len(all_strokes_to_delete)):
                    # for each stroke deletion step of the lesioned sketch, compute percentage of strokes deleted and similarity between that version and the intact version of the adjacent repetition
                    #percentage_deleted = float(num_deleted) / float(total_num_strokes)
                    feature_ind_of_deleted_sketch = all_strokes_to_delete[(all_strokes_to_delete['num_strokes_deleted'] == num_deleted)]['feature_ind'].unique()[0]
                    similarity = compute_similarity_2(Fs, F, [feature_ind_of_paired_sketch, feature_ind_of_deleted_sketch])
                    length = arcLengths[num_deleted]
                    df_to_add = pd.DataFrame([[g, t, num_deleted, total_num_strokes, length, similarity, rep]], columns=['gameID', 'target', 'deleted_stroke_number', 'total_num_strokes', 'length', 'similarity', 'base_rep'])
                    d = d.append(df_to_add)
    return d
            
############################################################################################### 



import ast 
import PIL.Image
from svgpathtools import parse_path
import svgpathtools
import math
import ast 

def arcl(svg):
    return parse_path(svg).length()
def getArcLengths(svgListString):
    return [arcl(ast.literal_eval(svgListString)[i]) for i in range(len(ast.literal_eval(svgListString)))]



############################################################################################### 
### Self-similarity individual sketches 
## run3_0286-a442ec93-ad78-42fa-b3e9-083da9a64c4d_6_repeated_waiting_03_0_end_0.png
def plot_self_similarity_of(df, sketch_dir, png_name):
    gameID = png_name.split('.')[0].split('_')[1]
    target = png_name.split('.')[0].split('_')[4] + png_name.split('.')[0].split('_')[5]
    repetition = png_name.split('.')[0].split('_')[6]
    d = df[(df['gameID'] == gameID) & (df['target'] == target) & (df['base_rep'] == int(repetition))]
    total_num_strokes = list(d['total_num_strokes'])[0]
    png_name_first = png_name.split('.')[0].split('_')[0] + '_' + png_name.split('.')[0].split('_')[1] + '_'\
                    + png_name.split('.')[0].split('_')[2] + '_'+ png_name.split('.')[0].split('_')[3]+ '_' \
                    + png_name.split('.')[0].split('_')[4] + '_'+ png_name.split('.')[0].split('_')[5]+ '_'\
                    + png_name.split('.')[0].split('_')[6]
    grid = plt.GridSpec(5, total_num_strokes, wspace=0.1, hspace=0.1)
    line_plot_height = 3
    width = 1.5 * total_num_strokes 
    plt.figure(figsize=(width,7.5))
        # Call plot() method on the appropriate object
    for direction in ['start', 'end']:
        color = 'lightcoral' if direction == 'start' else 'turquoise'
        num_row = line_plot_height if direction == 'start' else line_plot_height + 1
        d_ = d[d['direction'] == direction]
        a = sns.lineplot(x="num_strokes_deleted", y='similarity', data=d_, ax=plt.subplot(grid[0:line_plot_height, 0:]), color=color)
        plt.subplot(grid[0:line_plot_height, 0:]).set_xticks([])
        plot_num = 0
        for num_strokes_deleted in range(total_num_strokes):
            plot_num +=1
            png_name = png_name_first + '_' + direction + '_' + str(num_strokes_deleted) + '.png'
            path = os.path.join(os.path.join(sketch_dir, 'stroke_analysis/png'), png_name)
            im = Image.open(path)
            cropped_im = im.crop((350, 150, 600, 400))
            numReps = total_num_strokes
            # ax[1].plot(x, np.cos(x));
            #p = plt.subplot(num_row, num_strokes_deleted+1, 1)
            for spine in plt.subplot(grid[num_row, num_strokes_deleted]).spines.values():
                spine.set_edgecolor(color)
            p = plt.subplot(grid[num_row, num_strokes_deleted]).imshow(im)
            sns.set_style('white')
            plt.subplot(grid[num_row, num_strokes_deleted]).set_xticks([])
            plt.subplot(grid[num_row, num_strokes_deleted]).set_yticks([])
            
            
############################################################################################### 
# Coloring strokes based on stroke importance
from matplotlib import colors
from svgpathtools import parse_path, wsvg, svg2paths
def get_stroke_importance(df, sketch_dir, png_name):
    stroke_dir = os.path.join(sketch_dir, 'single_color')
    gameID = png_name.split('.')[0].split('_')[1]
    target = png_name.split('.')[0].split('_')[4] + png_name.split('.')[0].split('_')[5]
    target_ = png_name.split('.')[0].split('_')[4] + '_' + png_name.split('.')[0].split('_')[5]
    repetition = png_name.split('.')[0].split('_')[6]
    d = df[(df['gameID'] == gameID) & (df['target'] == target) & (df['base_rep'] == int(repetition))]
    total_num_strokes = list(d['total_num_strokes'])[0]
    max_similarity = np.max(np.array(d['similarity']))
    min_similarity = np.min(np.array(d['similarity']))
    norm = colors.Normalize(vmin=min_similarity, vmax=max_similarity)
    cmap = plt.cm.get_cmap('viridis')
    stroke_colors = []
    svg_list = ast.literal_eval(D[(D['gameID'] == gameID) & (D['repetition'] == int(repetition)) & (D['target'] == target_)]['svgString'].unique()[0])
    for stroke_num in range(len(svg_list)):
        similarity = d[d['num_strokes_deleted'] == stroke_num]['similarity'].unique()[0]
        rgba = cmap(1 - norm(similarity))
        color=colors.to_hex(rgba)
        stroke_colors.append(color)
    stroke_and_direction = '_coloring.svg'  # deleting which stroke? 
    stroke_level_path = png_name.split('.')[0] + stroke_and_direction
    parsed = [parse_path(svg_list[i]) for i in range(len(svg_list))]
    srh.render_svg_color(parsed, stroke_colors, base_dir=stroke_dir, out_fname=stroke_level_path)
    svg_paths = srh.generate_svg_path_list(os.path.join(stroke_dir,'svg'))
    srh.svg_to_png(svg_paths,base_dir=stroke_dir)
    last_path = stroke_level_path.split('.')[0]+ '.png'
    path = os.path.join(stroke_dir,'png',last_path)
    im = Image.open(path)
    plt.imshow(im)
    
    
    
###############################################################################################  
    
def get_pixel_importance_heatmaps(D, shapenet_ids):
    composite_heatmaps = []
    numerator_heatmaps = []
    denominator_heatmaps = []
    for lesioned_target in shapenet_ids:
        print ("getting map for {}".format(lesioned_target))
        numerator = np.zeros((224, 224))
        denominator = np.zeros((224, 224))
        composite = np.zeros((224, 224))
        counts = np.zeros((224, 224))
        D_target = D[D['lesioned_target'] == lesioned_target]
        to_compare_to = [s for s in shapenet_ids if s  != lesioned_target]
        sim_arr_itself = np.reshape(D_target[D_target['intact_target'] == lesioned_target].sort_values(['x', 'y'])['similarity'].values[:-1], (169, 169))
        sim_arrs_others = [np.reshape(D_target[D_target['intact_target'] == compare_to].sort_values(['x', 'y'])['similarity'].values[:-1], (169, 169)) for compare_to in to_compare_to]
        nan_others = [D_target[D_target['intact_target'] == compare_to].sort_values(['x', 'y'])['similarity'].values[-1] for compare_to in to_compare_to]                  
        for i in range(224 - 56 + 1): # i is the x coordinate 
            for j in range(224 - 56 + 1): # j is the y coordinate 
                # numerator 
                similarity_to_itself = sim_arr_itself[i][j]
                assert not np.isnan(similarity_to_itself)
                # denominator `
                similarities_to_others_lesioned = []
                similarities_to_others_intact = []
                for which, compare_to in enumerate(to_compare_to):
                    similarity_to_other_lesioned = sim_arrs_others[which][i][j]
                    assert not np.isnan(similarity_to_other_lesioned)
                    similarities_to_others_lesioned.append(float(similarity_to_other_lesioned))
                    similarity_to_other_intact = nan_others[which]
                    assert not np.isnan(similarity_to_other_intact)
                    similarities_to_others_intact.append(float(similarity_to_other_intact))
                #relative_similarities = [abs(similarities_to_others_lesioned[p] - similarities_to_others_intact[p]) for p in range(len(similarities_to_others_intact))]
                relative_similarities = [(float(similarities_to_others_lesioned[p]) - float(similarities_to_others_intact[p])) / float(similarities_to_others_intact[p]) for p in range(len(similarities_to_others_intact))]
                average_relative_similarity = 100* np.mean(np.array(relative_similarities)) # 100 * 
                if average_relative_similarity == 0:
                    average_relative_similarity = 0.05
                assert not np.isnan(average_relative_similarity)
                similarity_ratio = float(similarity_to_itself) / float(average_relative_similarity)
                assert not np.isnan(similarity_ratio)
                for x in range(56):
                    for y in range(56):
                        numerator[j + y, i + x] += float(similarity_to_itself)
                        denominator[j + y, i + x] += float(average_relative_similarity)
                        #composite[j + y, i + x] += float(similarity_ratio)
                        counts[j + y, i + x] += 1.0
        assert not np.isnan(numerator).any()
        assert not np.isnan(denominator).any()
        assert not np.isnan(composite).any()
        assert not np.isnan(counts).any()
        if np.any(counts[:, :] == 0):
            print(lesioned_target)
            print(counts)
        numerator_heatmap = numerator / counts # this is where nan appears 
        assert not np.isnan(numerator_heatmap).any()
        denominator_heatmap = denominator / counts 
        assert not np.isnan(denominator_heatmap).any()
        composite_heatmap = numerator_heatmap / denominator_heatmap
        assert not np.isnan(composite_heatmap).any()
        numerator_heatmaps.append(numerator_heatmap)
        denominator_heatmaps.append(denominator_heatmap)
        composite_heatmaps.append(composite_heatmap)
    return composite_heatmaps, numerator_heatmaps, denominator_heatmaps 

############################################################################################### 

############################################################################################### 

############################################################################################### 

############################################################################################### 
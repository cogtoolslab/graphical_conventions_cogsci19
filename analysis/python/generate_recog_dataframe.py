from __future__ import absolute_import, division

import os
import urllib, cStringIO

import pymongo as pm

import numpy as np
import scipy.stats as stats
import pandas as pd
import json
import re

from PIL import Image
import base64
import sys
from collections import Counter

import  matplotlib
from matplotlib import pylab, mlab, pyplot
# %matplotlib inline
# from IPython.core.pylabtools import figsize, getfigs
plt = pyplot
import seaborn as sns
sns.set_context('talk')
sns.set_style('darkgrid')

# from IPython.display import clear_output

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

# directory & file hierarchy
proj_dir = os.path.abspath('../../..')
analysis_dir = os.getcwd()
results_dir = os.path.join(proj_dir,'results')
stimuli_dir = os.path.join(proj_dir,'stimuli')
plot_dir = os.path.join(results_dir,'plots')
csv_dir = os.path.join(results_dir,'csv')
exp_dir = os.path.abspath(os.path.join(proj_dir,'experiments'))
sketch_dir = os.path.abspath(os.path.join(proj_dir,'sketches'))

## add helpers to python path
if os.path.join(proj_dir,'analysis','python') not in sys.path:
    sys.path.append(os.path.join(proj_dir,'analysis','python'))

if not os.path.exists(results_dir):
    os.makedirs(results_dir)

if not os.path.exists(plot_dir):
    os.makedirs(plot_dir)

if not os.path.exists(csv_dir):
    os.makedirs(csv_dir)

# Assign variables within imported analysis helpers
import analysis_helpers as h
if sys.version_info[0]>=3:
    from importlib import reload
reload(h)

# set vars
auth = pd.read_csv('auth.txt', header = None) # this auth.txt file contains the password for the sketchloop user
pswd = auth.values[0][0]
user = 'sketchloop'
host = 'rxdhawkins.me' ## cocolab ip address

# have to fix this to be able to analyze from local
import pymongo as pm
conn = pm.MongoClient('mongodb://sketchloop:' + pswd + '@127.0.0.1')
db = conn['3dObjects']
coll = db['graphical_conventions_recog']

# which iteration name should we use?
iterationName = 'pilot3'

## list of researchers
researchers = ['A4SSYO0HDVD4E', 'A1BOIDKD33QSDK','A1MMCS8S8CTWKU']
num_correct_thresh = 0
num_catch_correct_thresh = 4

## get list of valid sessions with reasonable accuracy
workers = coll.find({ '$and': [{'iterationName':iterationName}]}).distinct('workerId')
workers = [i for i in workers if len(i)>10 and i not in researchers] ## filter workers
print '{} workers performed this task'.format(len(workers))

## get total number of recog events in the collection as a whole
top_workers = []
catch_passable = []
for i,w in enumerate(workers):
    print 'Analyzing {} | {} of {}'.format(w,str(i).zfill(3),len(workers))
    clear_output(wait=True)
    R = coll.find({ '$and': [{'iterationName':iterationName}, {'workerId': w}]}).sort('time',-1)
    if R.count()==45:
        num_correct = coll.find({ '$and': [{'iterationName':iterationName}, {'workerId': w},{'catch_trial':False},{'correct':1}]}).sort('time',-1).count()
        num_catch_trial_correct = coll.find({ '$and': [{'iterationName':iterationName}, {'workerId': w},{'catch_trial':True},{'correct':1}]}).sort('time',-1).count()
        num_catch_trials_shown = coll.find({ '$and': [{'iterationName':iterationName}, {'workerId': w},{'catch_trial':True}]}).sort('time',-1).count()
        catch_passable.append(num_catch_trial_correct)
        ## make sure: (1) num correct was higher than thresh, (2) all 5 catch trials showed,
        ## (3) catch trials were correct above threshold, and (4) it was a full session
        if (num_correct >= num_correct_thresh) & (num_catch_trials_shown==5) & \
            (num_catch_trial_correct >= num_catch_correct_thresh):
                top_workers.append(w)

print '{} workers got at least {} experimental trials correct and {} catch trials correct and finished the entire HIT.'.format(len(top_workers),num_correct_thresh, num_catch_correct_thresh)
print '{} workers out of {} who finished the HIT got fewer than the threshold correct.'.format(np.sum(np.array(catch_passable)<num_catch_correct_thresh), len(catch_passable))

## get total number of recog events in the collection as a whole
# grab rep & accuracy
rep = []
correct = []
rt = []
condition = []
orig_correct = []
generalization = []
target = []
distractor1 = []
distractor2 = []
distractor3 = []
orig_gameID = []
gameID = []
version = [] ## yoked vs. scrambled40 vs. scrambled 10
recog_id = []
for i,w in enumerate(top_workers):
    print 'Now analyzing {} | {} of {}'.format(w,str(i+1).zfill(3), len(top_workers))
    clear_output(wait=True)
    R = coll.find({ '$and': [{'iterationName':iterationName}, {'workerId': w},{'catch_trial':False}]}).sort('time')
    for r in R:
        rep.append(r['repetition'])
        correct.append(r['correct'])
        rt.append(r['rt'])
        condition.append(r['condition'])
        if 'outcome' in r.keys():
            orig_correct.append(r['outcome'])
        else:
            orig_correct.append(r['original_correct'])
        generalization.append(r['Generalization'])
        target.append(r['target'])
        distractor1.append(r['distractor1'])
        distractor2.append(r['distractor2'])
        distractor3.append(r['distractor3'])
        orig_gameID.append(r['sketch'].split('_')[0])
        gameID.append(r['gameID'])
        version.append(r['version'])
        recog_id.append(r['recog_id'])

### make dataframe
X = pd.DataFrame([rep,correct,rt,condition,orig_correct,\
                 generalization,target,distractor1,distractor2,\
                 distractor3,orig_gameID,gameID,version,recog_id])
X = X.transpose()
X.columns = ['repetition','correct','rt','condition', 'orig_correct',\
             'generalization','target','distractor1','distractor2',\
             'distractor3','orig_gameID','gameID','version','recog_id']

## convert datatypes to numeric
X['correct'] = pd.to_numeric(X['correct'])
X['rt'] = pd.to_numeric(X['rt'])
X['orig_correct'] = pd.to_numeric(X['orig_correct'])

print 'Finished analyzing top workers.'
print 'There are {} observation in the dataframe.'.format(X.shape[0])

## function to unroll target, distractor dicts into separate columns
def dict2cols(X,item='target'):
    '''
    X = dataframe containing group data
    item = which item column to unroll: target? distractor1?
    '''
    df = pd.DataFrame.from_dict(X[item]) ## make temporary dataframe with dictionary as main column
    df2 = df[item].apply(pd.Series) ## separate into different columns
    ## rename to ensure uniqueness
    df3 = df2.rename(columns={'objectname': '{}_objectname'.format(item),\
                              'shapenetid': '{}_shapenetid'.format(item),\
                              'url': '{}_url'.format(item)})
    X2 = X.join(df3) ## add to original group dataframe
    X2.drop(labels=[item],axis=1,inplace=True) ## remove old dictionary column
    return X2

## now actually apply unrolling function
items = ['target','distractor1','distractor2','distractor3']
for item in items:
    print 'Unrolling {}'.format(item)
    clear_output(wait=True)
    if item in X.columns:
        X = dict2cols(X,item=item)

print 'Finished unrolling item dictionaries into separate columns.'

# ## view recognizability by repetition in tabular form
# X.groupby(['condition','repetition'])['correct'].mean()
#
# ## how many games from each version were finished?
# X.groupby('version')['repetition'].count()/40

## save out raw version of dataframe
X.to_csv(os.path.join(results_dir,'graphical_conventions_recog_data_raw.csv'),index=False)

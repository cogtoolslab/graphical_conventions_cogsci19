#!/usr/bin/python2.7
from __future__ import division

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

# import matplotlib
# from matplotlib import pylab, mlab, pyplot
# %matplotlib inline
# from IPython.core.pylabtools import figsize, getfigs
# plt = pyplot
# import seaborn as sns
# sns.set_context('talk')
# sns.set_style('white')

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")


'''
To generate main dataframe from pymongo database, run, e.g.:

python generate_dataframe.py

'''


# directory & file hierarchy
proj_dir = os.path.abspath('../../..')
analysis_dir = os.getcwd()
results_dir = os.path.join(proj_dir,'results')
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
import df_generation_helpers as h
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
coll = db['graphical_conventions']

# which iteration name should we use?
iterationName1 = 'run3_size4_waiting'
iterationName2 = 'run4_generalization'

## list of researcher mturk worker ID's to ignore
jefan = ['A1MMCS8S8CTWKU','A1MMCS8S8CTWKV','A1MMCS8S8CTWKS']
hawkrobe = ['A1BOIDKD33QSDK']
megsano = ['A1DVQQLVZR7W6I']
researchers = jefan + hawkrobe + megsano

## run 3 - get total number of stroke and clickedObj events in the collection as a whole
S1 = coll.find({ '$and': [{'iterationName':iterationName1}, {'eventType': 'stroke'}]}).sort('time')
C1 = coll.find({ '$and': [{'iterationName':iterationName1}, {'eventType': 'clickedObj'}]}).sort('time')

## run 4 - get total number of stroke and clickedObj events in the collection as a whole
S2 = coll.find({ '$and': [{'iterationName':iterationName2}, {'eventType': 'stroke'}]}).sort('time')
C2 = coll.find({ '$and': [{'iterationName':iterationName2}, {'eventType': 'clickedObj'}]}).sort('time')

print str(S1.count() + S2.count()) + ' stroke records in the database.'
print str(C1.count() + S2.count()) + ' clickedObj records in the database.' # previously 722 so 882 ideally

## get list of all candidate games
games = coll.distinct('gameid')

## get list of complete and valid games
run3_complete_games = h.get_complete_and_valid_games(games,coll,iterationName1,researchers=researchers, tolerate_undefined_worker=False)
run4_complete_games = h.get_complete_and_valid_games(games,coll,iterationName2,researchers=researchers, tolerate_undefined_worker=False)
## generate actual dataframe and get only valid games (filtering out games with low accuracy, timeouts)
D_run3 = h.generate_dataframe(coll, run3_complete_games, iterationName1, results_dir)
D_run4 = h.generate_dataframe(coll, run4_complete_games, iterationName2, results_dir)
## concatenate run3 and run4 dataframes
D = pd.concat([D_run3, D_run4], axis=0)

## filter crazies and add column
D = h.find_crazies(D)

# write out csv to results dir
D.to_csv(os.path.join(results_dir, 'graphical_conventions_{}_{}.csv'))

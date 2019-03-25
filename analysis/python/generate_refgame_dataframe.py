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

'''
To generate main dataframe from pymongo database, run, e.g.:

exp1 = ['run3_size4_waiting', 'run4_generalization']
exp2 = ['run5_submitButton']


python generate_refgame_dataframe.py --iterationName run3_size4_waiting
python generate_refgame_dataframe.py --iterationName run4_generalization
python generate_refgame_dataframe.py --iterationName run5_submitButton

'''

# directory & file hierarchy
proj_dir = os.path.abspath('../../..')
analysis_dir = os.getcwd()
results_dir = os.path.join(proj_dir,'results')
plot_dir = os.path.join(results_dir,'plots')
csv_dir = os.path.join(results_dir,'csv')
exp_dir = os.path.abspath(os.path.join(proj_dir,'experiments'))
sketch_dir = os.path.abspath(os.path.join(proj_dir,'sketches'))

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

# list of researcher mturk worker ID's to ignore
jefan = ['A1MMCS8S8CTWKU','A1MMCS8S8CTWKV','A1MMCS8S8CTWKS']
hawkrobe = ['A1BOIDKD33QSDK']
megsano = ['A1DVQQLVZR7W6I']
researchers = jefan + hawkrobe + megsano

# Assign variables within imported analysis helpers
import df_generation_helpers as h
if sys.version_info[0]>=3:
    from importlib import reload

## add helpers to python path
if os.path.join(proj_dir,'analysis','python') not in sys.path:
    sys.path.append(os.path.join(proj_dir,'analysis','python'))

if not os.path.exists(results_dir):
    os.makedirs(results_dir)

if not os.path.exists(plot_dir):
    os.makedirs(plot_dir)

if not os.path.exists(csv_dir):
    os.makedirs(csv_dir)

if __name__ == '__main__':

	import argparse
	parser = argparse.ArgumentParser()


	parser.add_argument('--iterationName', type=str, \
									  help='options: run3_size4_waiting, run4_generalization, run5_submitButton', 
									  default='run5_submitButton')

	args = parser.parse_args()
	iterationName = args.iterationName

	## get total number of stroke and clickedObj events in the collection as a whole
	S = coll.find({ '$and': [{'iterationName':iterationName}, {'eventType': 'stroke'}]}).sort('time')
	C = coll.find({ '$and': [{'iterationName':iterationName}, {'eventType': 'clickedObj'}]}).sort('time')

	## get list of all candidate games
	all_games = coll.find({'iterationName':iterationName}).distinct('gameid')

	## get list of complete and valid games
	complete_games = h.get_complete_and_valid_games(all_games,coll,iterationName1,researchers=researchers, tolerate_undefined_worker=False)

	## generate actual dataframe and get only valid games (filtering out games with low accuracy, timeouts)
	D = h.generate_dataframe(coll, complete_games, iterationName, csv_dir)

	# ## filter crazies and add column
	D = h.find_crazies(D)

	## add features for recognition experiment
	D = h.add_recog_session_ids(D)
	D = h.add_distractors_and_shapenet_ids(D)

	## if generalization column still capitalized, fix it
	try:
		D = D.rename(index=str, columns={"Generalization": "generalization"})
	except:
		pass

	## filter out single low accuracy game
	D = D[D['low_acc'] != True]

	## assign extra columns to keep track of category/subset/condition combinations
	if iterationName=='run5_submitButton':
		D = D.assign(category_subset = pd.Series(D['category'] + D['subset']))
		D = D.assign(category_subset_condition = pd.Series(D['category'] + D['subset'] + D['condition']))

	# save out master dataframe
	D.to_csv(os.path.join(csv_dir, 'graphical_conventions_group_data_{}.csv'.format(iterationName)), index=False)

	## write out bis dataframe to results dir
	h.save_bis(D, csv_dir, iterationName)

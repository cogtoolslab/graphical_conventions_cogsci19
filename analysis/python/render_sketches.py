import numpy as np
import pandas as pd
import os, sys
import boto3
import botocore

import json
import re
import ast

from PIL import Image
import base64
import sys

import pymongo as pm
import argparse

import df_generation_helpers as h
import svg_rendering_helpers as srh

parser = argparse.ArgumentParser()
parser.add_argument('--experiment_name', type=str, 
	help='options: refgame1.2, refgame2.0', default='refgame1.2')

args = parser.parse_args()

def make_dir_if_not_exists(dir_name):   
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return dir_name

### set up paths, etc. 
proj_dir = os.path.abspath('../..')
stimulus_dir = os.getcwd()
analysis_dir = os.path.join(proj_dir,'analysis')
results_dir = os.path.join(proj_dir,'results')
plot_dir = os.path.join(results_dir,'plots')
csv_dir = os.path.join(results_dir,'csv')
exp_dir = os.path.abspath(os.path.join(proj_dir,'experiments'))

## add helpers to python path
if os.path.join(proj_dir,'utils') not in sys.path:
    sys.path.append(os.path.join(proj_dir,'utils'))
   
## create directories that don't already exist        
result = [make_dir_if_not_exists(i) for i in [results_dir, plot_dir, csv_dir]]

## name of experiment
this_experiment = args.experiment_name

## update name of sketch dir so sketches from each experiment are nested appropriately
sketch_dir = os.path.abspath(os.path.join(results_dir,'sketches',this_experiment))
png_dir = os.path.abspath(os.path.join(sketch_dir,'png'))
svg_dir = os.path.abspath(os.path.join(sketch_dir,'svg'))

## create directories that don't already exist        
result = [make_dir_if_not_exists(i) for i in [sketch_dir,png_dir,svg_dir]]

## extract appropriate filename suffix based on experiment name
experiment_dict = {'refgame1.2':'run3run4','refgame2.0':'run5_submitButton'}
exp_ext = experiment_dict[this_experiment]

path_to_group_data = os.path.join(csv_dir,'graphical_conventions_group_data_{}.csv'.format(exp_ext))
X = pd.read_csv(path_to_group_data)

## handle missing data (missing draw duration measurements)
X = h.preprocess_dataframe(X)

## remove unnecessary columns if they exist
if 'Unnamed: 0' in X.columns:
    X = X.drop(labels=['Unnamed: 0'], axis=1)
if 'row_index' in X.columns:
    X = X.drop(labels=['row_index'], axis=1)    

'''
#### To render sketches from SVG data

*Note*: You may need to install ImageMagick first. 
- To do this, follow this link to install from source: https://imagemagick.org/script/install-source.php

- You might run into an issue where the compiler can't find `parser.h`. To fix this, follow the instructions in this blogpost: https://medium.com/@maohua.ethan.wang/install-imagemagick-on-mac-with-options-d5a2174df62
    - We ended up needing to add the libxml location to CFLAGS, but then actually just added a with-xml=no option so we don't compile/install imagemagick the libxml delegate library... hopefully that is okay for our purposes. but if it is not, we'll have to revisit this later. -@jefan 11/6/2019
- Also consulted this forum: https://www.imagemagick.org/discourse-server/viewtopic.php?t=29261 

- Download imagemagick tar file.
- Go to where it was downloaded and run: `tar xzvf ImageMagick.tar.gz`
- Perhaps, when running the `./configure` command, add these options to make sure that the delegate libraries (namely jpeg, png) are also installed:
    - `./configure --enable-delegate-build --with-png=yes --with-jpeg=yes CFLAGS="-I//anaconda3/include/libxml2 -I//anaconda3/include" --with-xml=yes`
- `make clean; make`
- `make install`
- `make check` (optional to check installation)

- As of 5:37pm on 11/6/2019, it seems to work!
'''

## extract sketch identifying info
gseries = X['gameID'].map(str)
nseries = X['trialNum'].map(str).apply(lambda x: x.zfill(2))
tseries = X['target'].map(str)
rseries = X['repetition'].map(str).apply(lambda x: x.zfill(2))

## build list of image filenames
fname_list = ['{}_{}_{}'.format(i,j,k) for (i,j,k) in zip(gseries,tseries,rseries)]

## convert svg string strings into svg string list
svg_string_list = [ast.literal_eval(i) for i in X.svgString.values]

## render out svg & convert to png
for this_fname,this_svg in zip(fname_list,svg_string_list):    
	print('Rendering to SVG: {}'.format(this_fname))
	srh.render_svg(this_svg,base_dir=sketch_dir,out_fname= '{}.svg'.format(this_fname))    
    
## get svg path list for rendered out svg
svg_paths = srh.generate_svg_path_list(os.path.join(sketch_dir,'svg'))    

## convert all svg to png
srh.svg_to_png(svg_paths,base_dir=sketch_dir)

## check to make sure that the there are as many png as there are svg, 
## and that the number of svg matches the number of files we wanted to render out (fname_list)
def deborkify(x):
    return [i for i in x if i != '.DS_Store']

num_png_files = len(deborkify(os.listdir(os.path.join(sketch_dir,'png'))))
num_svg_files = len(deborkify(os.listdir(os.path.join(sketch_dir,'svg'))))
assert num_png_files == num_svg_files
assert num_svg_files == len(fname_list)

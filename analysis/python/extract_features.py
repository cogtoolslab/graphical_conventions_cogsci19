from __future__ import division

import torch
import torchvision.models as models
import torch.nn as nn
import torchvision.transforms as transforms
import torch.nn.functional as F
from torch.autograd import Variable

from sklearn.decomposition import PCA

from glob import glob
import os

import numpy as np
import pandas as pd
import json
import re

from PIL import Image
import base64

from embeddings import *

'''
To extract features, run, e.g.:

python extract_features.py --data='/data/jefan/graphical_conventions/sketches' --layer_ind=5 --data_type='sketch' --spatial_avg=True

'''

# retrieve sketch paths
def list_files(path, ext='png'):
    result = [y for x in os.walk(path) for y in glob(os.path.join(x[0], '*.%s' % ext))]
    return result

def check_invalid_sketch(filenames,invalids_path='drawings_to_exclude.txt'):    
    if not os.path.exists(invalids_path):
        print('No file containing invalid paths at {}'.format(invalids_path))
        invalids = []        
    else:
        x = pd.read_csv(invalids_path, header=None)
        x.columns = ['filenames']
        invalids = list(x.filenames.values)
    valids = []   
    basenames = [f.split('/')[-1] for f in filenames]
    for i,f in enumerate(basenames):
        if f not in invalids:
            valids.append(filenames[i])
    return valids

def make_dataframe(RunNums,GameIDs,TrialNums,Conditions,Targets,Repetitions):    
    Y = pd.DataFrame([RunNums,GameIDs,TrialNums,Conditions,Targets,Repetitions])
    Y = Y.transpose()
    Y.columns = ['run_num','gameID','trial_num','condition','target','repetition']
    return Y

def normalize(X):
    X = X - X.mean(0)
    X = X / np.maximum(X.std(0), 1e-5)
    return X

def preprocess_features(Features, Y):
    _Y = Y.sort_values(['run_num','gameID','repetition','target'])
    inds = np.array(_Y.index)
    _Features = normalize(Features[inds])
    _Y = _Y.reset_index(drop=True) # reset pandas dataframe index
    return _Features, _Y

def save_features(Features, Y, layer_num, data_type, out_dir='/data/jefan/graphical_conventions/features'):
    if not os.path.exists('./features'):
        os.makedirs('./features')
    layers = ['P1','P2','P3','P4','P5','FC6','FC7']
    np.save(os.path.join(out_dir,'FEATURES_{}_{}.npy'.format(layers[int(layer_num)], data_type)), Features)
    np.savetxt(os.path.join(out_dir,'FEATURES_{}_{}.txt'.format(layers[int(layer_num)], data_type)), Features, delimiter=',') ## also save as txt file
    Y.to_csv(os.path.join(out_dir,'METADATA_{}.csv'.format(data_type)), index=True, index_label='feature_ind')
    print('Saved features out to {}!'.format(out_dir))
    return layers[int(layer_num)]

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

def apply_pca_and_save(F, layer_num, data_type, num_pcs = 512, out_dir='/data/jefan/graphical_conventions/features'):
    pca = PCA(n_components=num_pcs)
    pca.fit(F)
    print('Applying PCA and transforming data, using {} components'.format(num_pcs))
    F_ = pca.fit_transform(F)      
    np.save(os.path.join(out_dir,'FEATURES_{}_{}_PCA_{}.npy'.format(layers[int(layer_num)], data_type, num_pcs)), F_)
    np.savetxt(os.path.join(out_dir,'FEATURES_{}_{}_PCA_{}.txt'.format(layers[int(layer_num)], data_type, num_pcs)), F_, delimiter=',')    
    print('Saved PC-transformed features out to {}!').format(out_dir)
    return F_  


if __name__ == "__main__":
    import argparse
    proj_dir = os.path.abspath('../..')
    sketch_dir = os.path.abspath(os.path.join(proj_dir,'sketches'))
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, help='full path to images', \
                        default=os.path.join(sketch_dir,'combined'))
    parser.add_argument('--layer_ind', help='fc6 = 5, fc7 = 6', default=5)
    parser.add_argument('--num_pcs', help='number of principal components', default=512)    
    parser.add_argument('--data_type', help='"images" or "sketch"', default='images')
    parser.add_argument('--out_dir', help='path to save features to', default='/data/jefan/graphical_conventions/features')    
    parser.add_argument('--spatial_avg', type=bool, help='collapse over spatial dimensions, preserving channel activation only if true', default=True)     
    parser.add_argument('--crop_sketch', type=str2bool, help='do we crop sketches by default?', default='False')     
    parser.add_argument('--test', type=str2bool, help='testing only, do not save features', default='False')  
    parser.add_argument('--ext', type=str, help='image extension type (e.g., "png")', default="png")    

    args = parser.parse_args()
        
    ## get list of all sketch paths
    image_paths = sorted(list_files(args.data,args.ext))
    print('Length of image_paths before filtering: {}'.format(len(image_paths)))
    
    ## filter out invalid sketches
    image_paths = check_invalid_sketch(image_paths)
    print('Length of image_paths after filtering: {}'.format(len(image_paths)))    
    
    ## extract features
    layers = ['P1','P2','P3','P4','P5','FC6','FC7']
    extractor = FeatureExtractor(image_paths,layer=args.layer_ind,\
                                 data_type=args.data_type,\
                                 spatial_avg=args.spatial_avg,\
                                 crop_sketch=args.crop_sketch)
    Features,RunNums,GameIDs,\
    TrialNums,Conditions,Targets,Repetitions = extractor.extract_feature_matrix()   
    
    # organize metadata into dataframe
    Y = make_dataframe(RunNums,GameIDs,TrialNums,Conditions,Targets,Repetitions)
    _Features, _Y = preprocess_features(Features, Y)

    if args.test==False:
        layer = save_features(_Features, _Y, args.layer_ind, args.data_type,out_dir = args.out_dir)   
        _Features_PCA = apply_pca_and_save(_Features, args.layer_ind, args.data_type, num_pcs = args.num_pcs, out_dir=args.out_dir)
       

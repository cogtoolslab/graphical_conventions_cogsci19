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

from embeddings_images import *

'''
To extract features, run, e.g.:

python extract_features.py --data='/home/jefan/graphical_conventions/results/sketches/refgame1.2/png' --layer_ind=5 --data_type='sketch' --out_dir='/mnt/pentagon/data/share/graphical_conventions/features/refgame1.2/'

python extract_features.py --data='/home/jefan/graphical_conventions/results/sketches/refgame2.0/png' --layer_ind=5 --data_type='sketch' --out_dir='/mnt/pentagon/data/share/graphical_conventions/features/refgame2.0/'

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

def save_features(features, meta, args):
    features_fname = '' 
    layers = ['P1','P2','P3','P4','P5','FC6','FC7']
    layer_name = layers[int(args.layer_ind)]
    features_fname = 'FEATURES_vgg_{}'.format(layer_name)
    np.save(os.path.join(args.out_dir,'{}.npy'.format(features_fname)), 
            features)
    meta.to_csv(os.path.join(args.out_dir,'METADATA.csv'), index=True, 
                index_label='feature_ind')
    print('Saved features out to {}!'.format(args.out_dir))

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


if __name__ == "__main__":
    import argparse
    proj_dir = os.path.abspath('../..')
    sketch_dir = os.path.abspath(os.path.join(proj_dir,'sketches'))
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, help='full path to images', \
                        default=os.path.join(sketch_dir,'combined'))
    parser.add_argument('--layer_ind', help='fc6 = 5, fc7 = 6', default=5)
    parser.add_argument('--num_pcs', help='number of principal components', default=512)  
    parser.add_argument('--cuda_device', help='device to use', default=0)  
    parser.add_argument('--data_type', help='"images" or "sketch"', default='images')
    parser.add_argument('--out_dir', help='path to save features to', default='/data/jefan/graphical_conventions/features')    
    parser.add_argument('--spatial_avg', type=bool, help='collapse over spatial dimensions, preserving channel activation only if true', default=True) 
    parser.add_argument('--channel_norm', type=str2bool, help='apply channel-wise normalization?', default='True')    
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
    extractor = FeatureExtractor(image_paths,layer=args.layer_ind,\
                                 data_type=args.data_type,\
                                 cuda_device = args.cuda_device,\
                                 spatial_avg=args.spatial_avg)
    #Features,RunNums,GameIDs,\
    #TrialNums,Conditions,Targets,Repetitions = extractor.extract_feature_matrix(True)   
    features, paths = extractor.extract_feature_matrix(False) # changed 
    meta = pd.DataFrame({'path' : list(extractor.flatten_list(paths))})
    if args.test==False:        
        save_features(features, meta, args)

from __future__ import absolute_import, division, print_function
import os
import ast
#import urllib, cStringIO

import pymongo as pm

import numpy as np
import scipy.stats as stats
import pandas as pd
import json
import re

from PIL import Image
import base64
import sys

import matplotlib
from matplotlib import pylab, mlab, pyplot
from IPython.core.pylabtools import figsize, getfigs
plt = pyplot
import seaborn as sns
sns.set_context('talk')
sns.set_style('white')

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
warnings.filterwarnings('ignore')

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
import analysis_helpers as h
if sys.version_info[0]>=3:
    from importlib import reload
reload(h)

# import svg_rendering_helpers as srh
# reload(srh)

D = pd.read_csv(os.path.join(results_dir, 'graphical_conventions.csv'))

# Shapenet 
shapenets = []
shapenet_30afd2ef2ed30238aa3d0a2f00b54836 = {'filename': "30afd2ef2ed30238aa3d0a2f00b54836.png" , 'basic': "dining", 'subordinate': "dining_00" , 'subset':"A", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/30afd2ef2ed30238aa3d0a2f00b54836.png"}#,width: 256, height: 256};
shapenets.append(shapenet_30afd2ef2ed30238aa3d0a2f00b54836)
shapenet_30dc9d9cfbc01e19950c1f85d919ebc2 = {'filename': "30dc9d9cfbc01e19950c1f85d919ebc2.png" , 'basic': "dining", 'subordinate': "dining_01" , 'subset':"A", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/30dc9d9cfbc01e19950c1f85d919ebc2.png"}#,width: 256, height: 256};
shapenets.append(shapenet_30dc9d9cfbc01e19950c1f85d919ebc2 )
shapenet_4c1777173111f2e380a88936375f2ef4 = {'filename': "4c1777173111f2e380a88936375f2ef4.png" , 'basic': "dining", 'subordinate': "dining_02" , 'subset':"B", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/4c1777173111f2e380a88936375f2ef4.png"}#,width: 256, height: 256};
shapenets.append(shapenet_4c1777173111f2e380a88936375f2ef4)
shapenet_3466b6ecd040e252c215f685ba622927 = {'filename': "3466b6ecd040e252c215f685ba622927.png" , 'basic': "dining", 'subordinate': "dining_03" , 'subset':"B", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/3466b6ecd040e252c215f685ba622927.png"}#,width: 256, height: 256};
shapenets.append(shapenet_3466b6ecd040e252c215f685ba622927)
shapenet_38f87e02e850d3bd1d5ccc40b510e4bd = {'filename': "38f87e02e850d3bd1d5ccc40b510e4bd.png" , 'basic': "dining", 'subordinate': "dining_04" , 'subset':"B", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/38f87e02e850d3bd1d5ccc40b510e4bd.png"}#,width: 256, height: 256};
shapenets.append(shapenet_38f87e02e850d3bd1d5ccc40b510e4bd)
shapenet_3cf6db91f872d26c222659d33fd79709 = {'filename': "3cf6db91f872d26c222659d33fd79709.png" , 'basic': "dining", 'subordinate': "dining_05" , 'subset':"B", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/3cf6db91f872d26c222659d33fd79709.png"}#,width: 256, height: 256};
shapenets.append(shapenet_3cf6db91f872d26c222659d33fd79709)
shapenet_3d7ebe5de86294b3f6bcd046624c43c9 = {'filename': "3d7ebe5de86294b3f6bcd046624c43c9.png" , 'basic': "dining", 'subordinate': "dining_06" , 'subset':"A", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/3d7ebe5de86294b3f6bcd046624c43c9.png"}#,width: 256, height: 256};
shapenets.append(shapenet_3d7ebe5de86294b3f6bcd046624c43c9)
shapenet_56262eebe592b085d319c38340319ae4 = {'filename': "56262eebe592b085d319c38340319ae4.png" , 'basic': "dining", 'subordinate': "dining_07" , 'subset':"A", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/56262eebe592b085d319c38340319ae4.png"}#,width: 256, height: 256};
shapenets.append(shapenet_56262eebe592b085d319c38340319ae4)
shapenet_1d1641362ad5a34ac3bd24f986301745 = {'filename': "1d1641362ad5a34ac3bd24f986301745.png" , 'basic': "waiting", 'subordinate': "waiting_00" , 'subset':"A", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/1d1641362ad5a34ac3bd24f986301745.png"}#,width: 256, height: 256};
shapenets.append(shapenet_1d1641362ad5a34ac3bd24f986301745)
shapenet_1da9942b2ab7082b2ba1fdc12ecb5c9e = {'filename': "1da9942b2ab7082b2ba1fdc12ecb5c9e.png" , 'basic': "waiting", 'subordinate': "waiting_01" , 'subset':"A", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/1da9942b2ab7082b2ba1fdc12ecb5c9e.png"}#,width: 256, height: 256};
shapenets.append(shapenet_1da9942b2ab7082b2ba1fdc12ecb5c9e)
shapenet_2448d9aeda5bb9b0f4b6538438a0b930 = {'filename': "2448d9aeda5bb9b0f4b6538438a0b930.png" , 'basic': "waiting", 'subordinate': "waiting_02" , 'subset':"B", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/2448d9aeda5bb9b0f4b6538438a0b930.png"}#,width: 256, height: 256};
shapenets.append(shapenet_2448d9aeda5bb9b0f4b6538438a0b930)
shapenet_23b0da45f23e5fb4f4b6538438a0b930 = {'filename': "23b0da45f23e5fb4f4b6538438a0b930.png" , 'basic': "waiting", 'subordinate': "waiting_03" , 'subset':"B", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/23b0da45f23e5fb4f4b6538438a0b930.png"}#,width: 256, height: 256};
shapenets.append(shapenet_23b0da45f23e5fb4f4b6538438a0b930)
shapenet_2b5953c986dd08f2f91663a74ccd2338 = {'filename': "2b5953c986dd08f2f91663a74ccd2338.png" , 'basic': "waiting", 'subordinate': "waiting_04" , 'subset':"B", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/2b5953c986dd08f2f91663a74ccd2338.png"}#,width: 256, height: 256};
shapenets.append(shapenet_2b5953c986dd08f2f91663a74ccd2338)
shapenet_2e291f35746e94fa62762c7262e78952 = {'filename': "2e291f35746e94fa62762c7262e78952.png" , 'basic': "waiting", 'subordinate': "waiting_05" , 'subset':"B", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/2e291f35746e94fa62762c7262e78952.png"}#,width: 256, height: 256};
shapenets.append(shapenet_2e291f35746e94fa62762c7262e78952)
shapenet_2eaab78d6e4c4f2d7b0c85d2effc7e09 = {'filename': "2eaab78d6e4c4f2d7b0c85d2effc7e09.png" , 'basic': "waiting", 'subordinate': "waiting_06" , 'subset':"A", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/2eaab78d6e4c4f2d7b0c85d2effc7e09.png"}#,width: 256, height: 256};
shapenets.append(shapenet_2eaab78d6e4c4f2d7b0c85d2effc7e09)
shapenet_309674bdec2d24d7597976c675750537 = {'filename': "309674bdec2d24d7597976c675750537.png" , 'basic': "waiting", 'subordinate': "waiting_07" , 'subset':"A", 'url': "https://s3.amazonaws.com/shapenet-graphical-conventions/309674bdec2d24d7597976c675750537.png"}#,width: 256, height: 256}
shapenets.append(shapenet_309674bdec2d24d7597976c675750537)

### compute similarity between images 
def get_lesion_image_df(D, M, F):
    d = pd.read_csv('diagnosticity_df_3cf6db91f872d26c222659d33fd79709.csv') # change accordingly
    needed_columns = ['lesioned_target', 'intact_target', 'similarity', 'x', 'y']
    d = d.drop([col for col in d.columns if col not in needed_columns], axis=1)
    feature_ind_loc = M.columns.get_loc('feature_ind')
    for target_shapenet in shapenets[6:]:
        target_shapenet_id = target_shapenet['filename'].split('.')[0]
        print ("similarity for {}".format(target_shapenet_id))
        M_target = M[M['shapenet'] == target_shapenet_id]
        M_lesioned = M_target[M_target['isLesioned'] == True]
        array_to_add = [] 
        for distractor_shapenet in shapenets:
            distractor_shapenet_id = distractor_shapenet['filename'].split('.')[0]
            print("distractor: {}".format(distractor_shapenet_id))
            M_distractor = M[M['shapenet'] == distractor_shapenet_id]
            feature_ind_of_intact_image = M_distractor[M_distractor['isLesioned'] == False].iat[0,feature_ind_loc]
            for i,m in M_lesioned.iterrows():
                feature_ind_of_lesioned_sketch = m['feature_ind']
                x = m['x']
                y = m['y']
                #M_intact = M[M['target'] == intact_num]
                similarity = h.compute_similarity(F, [feature_ind_of_intact_image, feature_ind_of_lesioned_sketch])
                # df_to_add = pd.DataFrame([[target_shapenet_id, distractor_shapenet_id, x, y, similarity]], columns=['lesioned_target', 'intact_target', 'x', 'y', 'similarity'])
                # d = d.append(df_to_add)   
                series = pd.Series([target_shapenet_id, distractor_shapenet_id, x, y, similarity], index=['lesioned_target', 'intact_target', 'x', 'y', 'similarity'])
                array_to_add.append(series)
        d = d.append(array_to_add, ignore_index=True)   
        d.to_csv('diagnosticity_df_{}.csv'.format(target_shapenet_id))
        print("saving diagnosticity_df_{}.csv".format(target_shapenet_id))
    array_to_add = []
    for target_shapenet in shapenets:
        target_shapenet_id = target_shapenet['filename'].split('.')[0]
        print("final for {}".format(target_shapenet_id))
        M_target = M[M['shapenet'] == target_shapenet_id]
        M_non_lesioned = M_target[M_target['isLesioned'] == False]
        feature_ind_of_non_lesioned_image = M_non_lesioned[M_non_lesioned['isLesioned'] == False].iat[0,feature_ind_loc]
        
        for distractor_shapenet in shapenets:
            distractor_shapenet_id = distractor_shapenet['filename'].split('.')[0]
            M_distractor = M[M['shapenet'] == distractor_shapenet_id]
            feature_ind_of_intact_image = M_distractor[M_distractor['isLesioned'] == False].iat[0,feature_ind_loc]
            similarity = h.compute_similarity(F, [feature_ind_of_intact_image, feature_ind_of_non_lesioned_image])
            series = pd.Series([target_shapenet_id, distractor_shapenet_id, float('nan'), float('nan'), similarity], index=['lesioned_target', 'intact_target', 'x', 'y', 'similarity'])
            array_to_add.append(series)
    d = d.append(array_to_add, ignore_index=True)   
    return d

reload(h)
base_path = '../../../data/features/'
path_to_feats_diagnosticity = base_path + 'diagnosticity/FEATURES_FC6_images--spatial_avg=True_no-channel-norm.npy'
path_to_meta_diagnosticity = base_path + 'diagnosticity/METADATA_images--spatial_avg=True.csv'
F_diagnosticity = np.load(path_to_feats_diagnosticity)
def clean_up_metadata(M):
    return (M.assign(feature_ind=pd.Series(range(len(M)))))
M_diagnosticity = clean_up_metadata(pd.read_csv(path_to_meta_diagnosticity))
# diagnosticity_df = get_lesion_image_df(D, M_diagnosticity, F_diagnosticity)

def get_and_plot_diagnosticity_heatmaps(shapenet_ids, D):
    composite_heatmaps, numerator_heatmaps, denominator_heatmaps = h.get_pixel_importance_heatmaps(D)
    sns.set_context('paper')
    fig, axes = plt.subplots(nrows=2, ncols=2)
    image_links = [shapenet['url'] for shapenet in shapenet_ids]
    for target_num in range(4):
        response = requests.get(image_links[target_num])
        im = Image.open(BytesIO(response.content))
        x = 0 if target_num == 0 or target_num == 1 else 1
        y = 0 if target_num == 0 or target_num == 2 else 1
        ax = axes[x, y]
        heatmap = heatmaps[target_num]
        sns.heatmap(heatmap, ax=ax)
        # turn off axes 
        ax.imshow(im)

if __name__ == "__main__":
	diagnosticity_df= get_lesion_image_df(D, M_diagnosticity, F_diagnosticity)
	diagnosticity_df.to_csv('diagnosticity_df.csv')


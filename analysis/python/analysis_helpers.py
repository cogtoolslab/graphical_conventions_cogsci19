from __future__ import division

import os
#import urllib, cStringIO

import json

import os
import pandas as pd
import numpy as np

from numpy import shape
from PIL import Image, ImageOps
import base64
from io import BytesIO
import requests

import ast 
import PIL.Image
from svgpathtools import parse_path
import svgpathtools
import math
import ast 

import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib import colors
import seaborn as sns
import re
sns.set_context('poster')
colors = sns.color_palette("cubehelix", 5)
from svgpathtools import parse_path, wsvg, svg2paths
from itertools import combinations

# directory & file hierarchy
proj_dir = os.path.abspath('../../..')
analysis_dir = os.getcwd()
results_dir = os.path.join(proj_dir,'results')

###############################################################################################
################### HELPERS FOR graphical conventions analysis notebook ####################################
###############################################################################################

#Dictionaries to convert between objects and categories

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
# pair number dictionary for shapenet pairs 
pair_num_dict = {('1d1641362ad5a34ac3bd24f986301745', '1da9942b2ab7082b2ba1fdc12ecb5c9e'): 0,
 ('1d1641362ad5a34ac3bd24f986301745', '23b0da45f23e5fb4f4b6538438a0b930'): 1,
 ('1d1641362ad5a34ac3bd24f986301745', '2448d9aeda5bb9b0f4b6538438a0b930'): 2,
 ('1d1641362ad5a34ac3bd24f986301745', '2b5953c986dd08f2f91663a74ccd2338'): 3,
 ('1d1641362ad5a34ac3bd24f986301745', '2e291f35746e94fa62762c7262e78952'): 4,
 ('1d1641362ad5a34ac3bd24f986301745', '2eaab78d6e4c4f2d7b0c85d2effc7e09'): 5,
 ('1d1641362ad5a34ac3bd24f986301745', '309674bdec2d24d7597976c675750537'): 6,
 ('1d1641362ad5a34ac3bd24f986301745', '30afd2ef2ed30238aa3d0a2f00b54836'): 7,
 ('1d1641362ad5a34ac3bd24f986301745', '30dc9d9cfbc01e19950c1f85d919ebc2'): 8,
 ('1d1641362ad5a34ac3bd24f986301745', '3466b6ecd040e252c215f685ba622927'): 9,
 ('1d1641362ad5a34ac3bd24f986301745', '38f87e02e850d3bd1d5ccc40b510e4bd'): 10,
 ('1d1641362ad5a34ac3bd24f986301745', '3cf6db91f872d26c222659d33fd79709'): 11,
 ('1d1641362ad5a34ac3bd24f986301745', '3d7ebe5de86294b3f6bcd046624c43c9'): 12,
 ('1d1641362ad5a34ac3bd24f986301745', '4c1777173111f2e380a88936375f2ef4'): 13,
 ('1d1641362ad5a34ac3bd24f986301745', '56262eebe592b085d319c38340319ae4'): 14,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '23b0da45f23e5fb4f4b6538438a0b930'): 15,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '2448d9aeda5bb9b0f4b6538438a0b930'): 16,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '2b5953c986dd08f2f91663a74ccd2338'): 17,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '2e291f35746e94fa62762c7262e78952'): 18,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '2eaab78d6e4c4f2d7b0c85d2effc7e09'): 19,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '309674bdec2d24d7597976c675750537'): 20,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '30afd2ef2ed30238aa3d0a2f00b54836'): 21,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '30dc9d9cfbc01e19950c1f85d919ebc2'): 22,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '3466b6ecd040e252c215f685ba622927'): 23,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '38f87e02e850d3bd1d5ccc40b510e4bd'): 24,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '3cf6db91f872d26c222659d33fd79709'): 25,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '3d7ebe5de86294b3f6bcd046624c43c9'): 26,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '4c1777173111f2e380a88936375f2ef4'): 27,
 ('1da9942b2ab7082b2ba1fdc12ecb5c9e', '56262eebe592b085d319c38340319ae4'): 28,
 ('23b0da45f23e5fb4f4b6538438a0b930', '2448d9aeda5bb9b0f4b6538438a0b930'): 29,
 ('23b0da45f23e5fb4f4b6538438a0b930', '2b5953c986dd08f2f91663a74ccd2338'): 30,
 ('23b0da45f23e5fb4f4b6538438a0b930', '2e291f35746e94fa62762c7262e78952'): 31,
 ('23b0da45f23e5fb4f4b6538438a0b930', '2eaab78d6e4c4f2d7b0c85d2effc7e09'): 32,
 ('23b0da45f23e5fb4f4b6538438a0b930', '309674bdec2d24d7597976c675750537'): 33,
 ('23b0da45f23e5fb4f4b6538438a0b930', '30afd2ef2ed30238aa3d0a2f00b54836'): 34,
 ('23b0da45f23e5fb4f4b6538438a0b930', '30dc9d9cfbc01e19950c1f85d919ebc2'): 35,
 ('23b0da45f23e5fb4f4b6538438a0b930', '3466b6ecd040e252c215f685ba622927'): 36,
 ('23b0da45f23e5fb4f4b6538438a0b930', '38f87e02e850d3bd1d5ccc40b510e4bd'): 37,
 ('23b0da45f23e5fb4f4b6538438a0b930', '3cf6db91f872d26c222659d33fd79709'): 38,
 ('23b0da45f23e5fb4f4b6538438a0b930', '3d7ebe5de86294b3f6bcd046624c43c9'): 39,
 ('23b0da45f23e5fb4f4b6538438a0b930', '4c1777173111f2e380a88936375f2ef4'): 40,
 ('23b0da45f23e5fb4f4b6538438a0b930', '56262eebe592b085d319c38340319ae4'): 41,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '2b5953c986dd08f2f91663a74ccd2338'): 42,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '2e291f35746e94fa62762c7262e78952'): 43,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '2eaab78d6e4c4f2d7b0c85d2effc7e09'): 44,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '309674bdec2d24d7597976c675750537'): 45,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '30afd2ef2ed30238aa3d0a2f00b54836'): 46,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '30dc9d9cfbc01e19950c1f85d919ebc2'): 47,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '3466b6ecd040e252c215f685ba622927'): 48,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '38f87e02e850d3bd1d5ccc40b510e4bd'): 49,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '3cf6db91f872d26c222659d33fd79709'): 50,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '3d7ebe5de86294b3f6bcd046624c43c9'): 51,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '4c1777173111f2e380a88936375f2ef4'): 52,
 ('2448d9aeda5bb9b0f4b6538438a0b930', '56262eebe592b085d319c38340319ae4'): 53,
 ('2b5953c986dd08f2f91663a74ccd2338', '2e291f35746e94fa62762c7262e78952'): 54,
 ('2b5953c986dd08f2f91663a74ccd2338', '2eaab78d6e4c4f2d7b0c85d2effc7e09'): 55,
 ('2b5953c986dd08f2f91663a74ccd2338', '309674bdec2d24d7597976c675750537'): 56,
 ('2b5953c986dd08f2f91663a74ccd2338', '30afd2ef2ed30238aa3d0a2f00b54836'): 57,
 ('2b5953c986dd08f2f91663a74ccd2338', '30dc9d9cfbc01e19950c1f85d919ebc2'): 58,
 ('2b5953c986dd08f2f91663a74ccd2338', '3466b6ecd040e252c215f685ba622927'): 59,
 ('2b5953c986dd08f2f91663a74ccd2338', '38f87e02e850d3bd1d5ccc40b510e4bd'): 60,
 ('2b5953c986dd08f2f91663a74ccd2338', '3cf6db91f872d26c222659d33fd79709'): 61,
 ('2b5953c986dd08f2f91663a74ccd2338', '3d7ebe5de86294b3f6bcd046624c43c9'): 62,
 ('2b5953c986dd08f2f91663a74ccd2338', '4c1777173111f2e380a88936375f2ef4'): 63,
 ('2b5953c986dd08f2f91663a74ccd2338', '56262eebe592b085d319c38340319ae4'): 64,
 ('2e291f35746e94fa62762c7262e78952', '2eaab78d6e4c4f2d7b0c85d2effc7e09'): 65,
 ('2e291f35746e94fa62762c7262e78952', '309674bdec2d24d7597976c675750537'): 66,
 ('2e291f35746e94fa62762c7262e78952', '30afd2ef2ed30238aa3d0a2f00b54836'): 67,
 ('2e291f35746e94fa62762c7262e78952', '30dc9d9cfbc01e19950c1f85d919ebc2'): 68,
 ('2e291f35746e94fa62762c7262e78952', '3466b6ecd040e252c215f685ba622927'): 69,
 ('2e291f35746e94fa62762c7262e78952', '38f87e02e850d3bd1d5ccc40b510e4bd'): 70,
 ('2e291f35746e94fa62762c7262e78952', '3cf6db91f872d26c222659d33fd79709'): 71,
 ('2e291f35746e94fa62762c7262e78952', '3d7ebe5de86294b3f6bcd046624c43c9'): 72,
 ('2e291f35746e94fa62762c7262e78952', '4c1777173111f2e380a88936375f2ef4'): 73,
 ('2e291f35746e94fa62762c7262e78952', '56262eebe592b085d319c38340319ae4'): 74,
 ('2eaab78d6e4c4f2d7b0c85d2effc7e09', '309674bdec2d24d7597976c675750537'): 75,
 ('2eaab78d6e4c4f2d7b0c85d2effc7e09', '30afd2ef2ed30238aa3d0a2f00b54836'): 76,
 ('2eaab78d6e4c4f2d7b0c85d2effc7e09', '30dc9d9cfbc01e19950c1f85d919ebc2'): 77,
 ('2eaab78d6e4c4f2d7b0c85d2effc7e09', '3466b6ecd040e252c215f685ba622927'): 78,
 ('2eaab78d6e4c4f2d7b0c85d2effc7e09', '38f87e02e850d3bd1d5ccc40b510e4bd'): 79,
 ('2eaab78d6e4c4f2d7b0c85d2effc7e09', '3cf6db91f872d26c222659d33fd79709'): 80,
 ('2eaab78d6e4c4f2d7b0c85d2effc7e09', '3d7ebe5de86294b3f6bcd046624c43c9'): 81,
 ('2eaab78d6e4c4f2d7b0c85d2effc7e09', '4c1777173111f2e380a88936375f2ef4'): 82,
 ('2eaab78d6e4c4f2d7b0c85d2effc7e09', '56262eebe592b085d319c38340319ae4'): 83,
 ('309674bdec2d24d7597976c675750537', '30afd2ef2ed30238aa3d0a2f00b54836'): 84,
 ('309674bdec2d24d7597976c675750537', '30dc9d9cfbc01e19950c1f85d919ebc2'): 85,
 ('309674bdec2d24d7597976c675750537', '3466b6ecd040e252c215f685ba622927'): 86,
 ('309674bdec2d24d7597976c675750537', '38f87e02e850d3bd1d5ccc40b510e4bd'): 87,
 ('309674bdec2d24d7597976c675750537', '3cf6db91f872d26c222659d33fd79709'): 88,
 ('309674bdec2d24d7597976c675750537', '3d7ebe5de86294b3f6bcd046624c43c9'): 89,
 ('309674bdec2d24d7597976c675750537', '4c1777173111f2e380a88936375f2ef4'): 90,
 ('309674bdec2d24d7597976c675750537', '56262eebe592b085d319c38340319ae4'): 91,
 ('30afd2ef2ed30238aa3d0a2f00b54836', '30dc9d9cfbc01e19950c1f85d919ebc2'): 92,
 ('30afd2ef2ed30238aa3d0a2f00b54836', '3466b6ecd040e252c215f685ba622927'): 93,
 ('30afd2ef2ed30238aa3d0a2f00b54836', '38f87e02e850d3bd1d5ccc40b510e4bd'): 94,
 ('30afd2ef2ed30238aa3d0a2f00b54836', '3cf6db91f872d26c222659d33fd79709'): 95,
 ('30afd2ef2ed30238aa3d0a2f00b54836', '3d7ebe5de86294b3f6bcd046624c43c9'): 96,
 ('30afd2ef2ed30238aa3d0a2f00b54836', '4c1777173111f2e380a88936375f2ef4'): 97,
 ('30afd2ef2ed30238aa3d0a2f00b54836', '56262eebe592b085d319c38340319ae4'): 98,
 ('30dc9d9cfbc01e19950c1f85d919ebc2', '3466b6ecd040e252c215f685ba622927'): 99,
 ('30dc9d9cfbc01e19950c1f85d919ebc2', '38f87e02e850d3bd1d5ccc40b510e4bd'): 100,
 ('30dc9d9cfbc01e19950c1f85d919ebc2', '3cf6db91f872d26c222659d33fd79709'): 101,
 ('30dc9d9cfbc01e19950c1f85d919ebc2', '3d7ebe5de86294b3f6bcd046624c43c9'): 102,
 ('30dc9d9cfbc01e19950c1f85d919ebc2', '4c1777173111f2e380a88936375f2ef4'): 103,
 ('30dc9d9cfbc01e19950c1f85d919ebc2', '56262eebe592b085d319c38340319ae4'): 104,
 ('3466b6ecd040e252c215f685ba622927', '38f87e02e850d3bd1d5ccc40b510e4bd'): 105,
 ('3466b6ecd040e252c215f685ba622927', '3cf6db91f872d26c222659d33fd79709'): 106,
 ('3466b6ecd040e252c215f685ba622927', '3d7ebe5de86294b3f6bcd046624c43c9'): 107,
 ('3466b6ecd040e252c215f685ba622927', '4c1777173111f2e380a88936375f2ef4'): 108,
 ('3466b6ecd040e252c215f685ba622927', '56262eebe592b085d319c38340319ae4'): 109,
 ('38f87e02e850d3bd1d5ccc40b510e4bd', '3cf6db91f872d26c222659d33fd79709'): 110,
 ('38f87e02e850d3bd1d5ccc40b510e4bd', '3d7ebe5de86294b3f6bcd046624c43c9'): 111,
 ('38f87e02e850d3bd1d5ccc40b510e4bd', '4c1777173111f2e380a88936375f2ef4'): 112,
 ('38f87e02e850d3bd1d5ccc40b510e4bd', '56262eebe592b085d319c38340319ae4'): 113,
 ('3cf6db91f872d26c222659d33fd79709', '3d7ebe5de86294b3f6bcd046624c43c9'): 114,
 ('3cf6db91f872d26c222659d33fd79709', '4c1777173111f2e380a88936375f2ef4'): 115,
 ('3cf6db91f872d26c222659d33fd79709', '56262eebe592b085d319c38340319ae4'): 116,
 ('3d7ebe5de86294b3f6bcd046624c43c9', '4c1777173111f2e380a88936375f2ef4'): 117,
 ('3d7ebe5de86294b3f6bcd046624c43c9', '56262eebe592b085d319c38340319ae4'): 118,
 ('4c1777173111f2e380a88936375f2ef4', '56262eebe592b085d319c38340319ae4'): 119}

################################################################################################
# shapenet chairs info 
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

################################################################################################

def clean_up_metadata(M):
    return (M.assign(feature_ind=pd.Series(range(len(M))))
             .assign(repetition=pd.to_numeric(M.repetition)))
             #drop(columns=['Unnamed: 0'])

###############################################################################################
    
def compute_similarity(F, inds_to_compare): # inds_to_compare: feature indices
    features_to_compare = F[inds_to_compare, :]
    CORRMAT = np.corrcoef(features_to_compare)
    similarity = np.mean(np.ma.masked_equal(np.tril(CORRMAT, -1), 0))
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
    return similarity

###############################################################################################

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

def get_image(shapenet_id, pad):
    image_link = 'https://s3.amazonaws.com/shapenet-graphical-conventions/' + shapenet_id + '.png'
    response = requests.get(image_link)
    im = Image.open(BytesIO(response.content))
    padding = (pad, pad, pad, pad)
    im = ImageOps.expand(im, padding)
    return im

############################################################################################### 

def get_pixel_importance_heatmap_pair(D, shapenet_pair, pad, kernel):
    padded_imsize = 224 + 2 * pad 
    denominator = np.zeros((padded_imsize, padded_imsize))
    counts = np.zeros((padded_imsize, padded_imsize))
    if (shapenet_pair[0], shapenet_pair[1]) in pair_num_dict:
        pair_num = pair_num_dict[(shapenet_pair[0], shapenet_pair[1])]
    else:
        pair_num = pair_num_dict[(shapenet_pair[1], shapenet_pair[0])]
    pair_df = D[D['pair_num'] == pair_num] 
    sim_arrs_others = np.array(pair_df['similarity'])[:-1]
    nan_others = np.array(pair_df['similarity'])[-1]                  
    for i in range(padded_imsize - kernel + 1): # i is the x coordinate 
        for j in range(padded_imsize - kernel + 1): # j is the y coordinate 
            similarity_to_other_lesioned = sim_arrs_others[225 * i + j]
            assert not np.isnan(similarity_to_other_lesioned)
            similarity_to_other_intact = nan_others
            assert not np.isnan(similarity_to_other_intact)
            relative_similarity = float(similarity_to_other_lesioned) - float(similarity_to_other_intact)
            for x in range(kernel):
                for y in range(kernel):
                    denominator[j + y, i + x] += relative_similarity
                    counts[j + y, i + x] += 1.0
    assert not np.isnan(denominator).any()
    assert not np.isnan(counts).any()
    denominator_heatmap = denominator / counts 
    assert not np.isnan(denominator_heatmap).any()
    return denominator_heatmap 
    
def get_pixel_importance_heatmaps_updated(D, shapenet_ids, pad, kernel):
    padded_imsize = 224 + 2 * pad 
    pair_heatmaps = {}
    pairs = list(combinations(shapenet_ids, 2))
    for pair in pairs:
        print("getting heatmap for pair: {} and {}".format(pair[0], pair[1]))
        pair_heatmaps[tuple(pair)] = get_pixel_importance_heatmap_pair(D, pair, pad, kernel)
    heatmaps = []
    for shapenet in shapenet_ids:
        heatmap = np.zeros((padded_imsize, padded_imsize))
        for distractor in shapenet_ids:
            if shapenet != distractor:
                 if (shapenet, distractor) in pair_heatmaps:
                     heatmap_part = pair_heatmaps[(shapenet, distractor)]
                 else:
                     heatmap_part = pair_heatmaps[(distractor, shapenet)]
                 heatmap += heatmap_part
        heatmaps.append(heatmap)
    return heatmaps 
############################################################################################### 
# function to plot heatmaps 
def plot_heatmaps(D, shapenet_ids, pad, kernel):
    denominator_heatmaps_updated = get_pixel_importance_heatmaps_updated(D, shapenet_ids, pad, kernel)
    sns.set_context('paper')
    fig, axes = plt.subplots(figsize=(len(shapenet_ids) * 4, 4), nrows=1, ncols=len(shapenet_ids))
    min_val = np.min(denominator_heatmaps_updated) 
    max_val = np.max(denominator_heatmaps_updated) 
    for target_num, target in enumerate(shapenet_ids):
        im = get_image(target, pad)
        ax = axes[target_num]
        heatmap = denominator_heatmaps_updated[target_num]
        hmax = sns.heatmap(heatmap, ax=ax, alpha = 0.20, vmin=min_val, vmax=max_val, center=0)
        ax.imshow(im)
        ax.axis('off')
    plt.show()
############################################################################################### 
# input: shapenet_ids, target_index
def get_all_heatmaps(shapenet_ids, target, target_index, distractors, pad, kernel, D):
    target_distractor_heatmaps = [get_pixel_importance_heatmap_pair(D, [target, distractor], pad, kernel) for distractor in distractors]
    multi_way_heatmap = get_pixel_importance_heatmaps_updated(D, shapenet_ids, pad, kernel)[target_index]
    all_heatmaps = target_distractor_heatmaps + [multi_way_heatmap]
    return all_heatmaps

def plot_heatmaps_complete(shapenet_ids, target_index, pad, kernel, D):
    sns.axes_style('white')
    fig, axes = plt.subplots(figsize=(16, 16), nrows=len(shapenet_ids), ncols=len(shapenet_ids))
    target = shapenet_ids[target_index]
    distractors = [shapenet_ids[i] for i in range(len(shapenet_ids)) if i != target_index] 
    all_heatmaps = get_all_heatmaps(shapenet_ids, target, target_index, distractors, pad, kernel, D)
    min_val = np.min(all_heatmaps)
    max_val = np.max(all_heatmaps) 
    im = get_image(shapenet_ids[target_index], pad)
    for i, heatmap in enumerate(all_heatmaps):
        ax=axes[i, 0]
        ax.imshow(im)
        with sns.axes_style("white"):
            hmax = sns.heatmap(heatmap, ax=ax, alpha = 0.20, vmin=min_val, vmax=max_val, center=0, linecolor='black')
    for i, distractor in enumerate(distractors):
        im = get_image(distractor, pad)
        ax=axes[i, i + 1]
        ax.imshow(im)
        ax=axes[len(shapenet_ids) - 1, i + 1]
        ax.imshow(im)
    for ax in fig.axes:
        ax.axis('off')
    plt.show()
    return all_heatmaps 
############################################################################################### 

def RGBA2RGB(image, color=(255, 255, 255)):
            """Alpha composite an RGBA Image with a specified color.
            Simpler, faster version than the solutions above.
            Source: http://stackoverflow.com/a/9459208/284318
            Keyword Arguments:
            image -- PIL RGBA Image object
            color -- Tuple r, g, b (default 255, 255, 255)
            """
            image.load()  # needed for split()
            background = Image.new('RGB', image.size, (0, 0, 0))
            background.paste(image, mask=image.split()[3])  # 3 is the alpha channel
            return background
        
def render_lesioned_images(pad, box_size):
    image_dir = os.path.join(sketch_dir,'diagnosticity_{}_intact'.format(str(box_size)))
    for target_num, shapenet in enumerate(shapenets):
        image_link = shapenet['url']
        shapenet_id = shapenet['filename'].split('.')[0]
        print('rendering lesioned version of {}'.format(shapenet_id))
        target = shapenet['subordinate']
        subset = shapenet['subset']
        response = requests.get(image_link)
        im = Image.open(BytesIO(response.content))
        im = RGBA2RGB(im)
        padding = (pad, pad, pad, pad)
        im = ImageOps.expand(im, padding)
        pixels = im.load()
        width, height = im.size
        for x in range(width - box_size + 1):
            for y in range(width - box_size + 1):
                new = im.copy()
                new_pixels = new.load()
                count = 0
                for i in range(width):
                    for j in range(height):
                        new_pixels[i,j] = pixels[i,j]
                for k in range(box_size): # for every pixel:
                    for l in range(box_size):
                        new_pixels[x + k, y + l] = (0, 0, 0)
                new.save(os.path.join(image_dir, '{}_{}_{}_lesioned_{}_{}_{}.png'.format(shapenet_id, target, subset, str(x), str(y), str(count))))
                count += 1
        im.save(os.path.join(image_dir, '{}_{}_{}_intact_{}_{}_{}.png'.format(shapenet_id, target, subset, '0', '0', '0')))
        
############################################################################################### 
        
        
        
from __future__ import division
import os
import numpy as np
from PIL import Image

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('--path_to_imgs', type=str, help='path to images to upload?', \
		default='./chairs1k_pilot_flattened') 	
	parser.add_argument('--out_path', type=str, help='name of path to save out to', \
		default='./chairs1k_pilot_flattened_cropped')
	parser.add_argument('--cropped_imsize', type=int, help='size of image to crop down to', \
		default=224)	
	args = parser.parse_args()

	## source path
	path_to_img = args.path_to_imgs

	## out path
	out_path = args.out_path

	## get list of all images
	_all_files = os.listdir(path_to_img)
	all_files = [i for i in _all_files if i != '.DS_Store'] ## mac nonsense
	print 'Total number of images: {}'.format(len(all_files))

	## get list of full image paths
	all_paths = [os.path.join(path_to_img,a) for a in all_files]

	## crop image to make sure it is square
	from PIL import Image
	runThis = 1
	if runThis:
	    rw = 224 # final width of images
	    rh = 224   
	    for i,path in enumerate(all_paths):
	        img = Image.open(path)
	        w = np.shape(img)[1] 
	        h = np.shape(img)[0]                     
	        img = img.crop( (int(w/2-rw/2),int(h/2-rh/2),int(w/2+rw/2),int(h/2+rh/2)) )
	        img.thumbnail([224, 224], Image.ANTIALIAS)                    
	        new_filename = path.split('/')[-1]
	        if not os.path.exists(out_path):
	            os.makedirs(out_path)
	        new_filepath = os.path.join(out_path,new_filename)
	        imagefile = open(new_filepath, 'wb')
	        try:
	            print 'Saving out cropped image: {}'.format(new_filepath)
	            img.save(imagefile, "png", quality=90)
	            imagefile.close()
	        except:
	            print "Cannot save user image"                                                        


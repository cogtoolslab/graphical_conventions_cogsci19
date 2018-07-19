import os
import boto
 
if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('--bucket_name', type=str, help='name of S3 bucket?', \
		default='shapenet-graphical-conventions')
	parser.add_argument('--path_to_imgs', type=str, help='path to images to upload?', \
		default='./chairs1k_pilot_flattened_cropped')   
	args = parser.parse_args()

	## tell user some useful information
	print 'Path to images is : {}'.format(args.path_to_imgs)    
	print 'Uploading to this bucket: {}'.format(args.bucket_name)

	## establish connection to s3 
	conn = boto.connect_s3()

	## create a bucket with the appropriate bucket name
	try: 
		b = conn.create_bucket(args.bucket_name) 
	except:
		b = conn.get_bucket(args.bucket_name) 

	## establish path to image data
	path_to_img = args.path_to_imgs

	## get list of image paths
	_all_files = os.listdir(path_to_img)
	all_files = [i for i in _all_files if i != '.DS_Store'] ## mac nonsense

	## now loop through image paths and actually upload to s3 
	for i,a in enumerate(all_files):
	    print 'Now uploading {} | {} of {}'.format(a,i,len(all_files))
	    try:
	    	k = b.new_key(a) ## if we need to overwrite this, we have to replace this line boto.get_key
	    except:
	    	k = b.get_key(a)
	    k.set_contents_from_filename(os.path.join(path_to_img,a))
	    k.set_acl('public-read')
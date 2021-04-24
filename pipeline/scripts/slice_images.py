'''
A simple code for preparing .fits "cutouts" of blank regions of sky to inject galfit models onto, in the context of uncertainty calculations.

'''
import configparser
import os
import shutil
import matplotlib.pyplot as plt
import re
from astropy.visualization.stretch import SinhStretch, LinearStretch
from astropy.visualization import ImageNormalize
from astropy.visualization import ZScaleInterval
import matplotlib.patches as patches
from astropy.stats import sigma_clipped_stats
from scipy import spatial
import numpy as np 
from astropy.stats import sigma_clip
from astropy.io import fits
import random
from smoother import maskBrightSource

def print_stage(line2print, ch='-'):
    '''
    Function that prints lines for organizational purposes in the code outputs.
    Parameters:
    -----------
    line2print: str, the message to be printed
    ch : str, the boundary dividing character of the message
    '''
    nl = len(line2print)
    print(ch*nl)
    print(line2print)
    print(ch*nl)
    print(' ')


def slice_sky(iniconf):
    '''
    Function that will generate slices of empty sky from a .fits image
    '''

    data_dir = iniconf['core info']['data_dir']
    output_dir = iniconf['core info']['output_dir']
    sky_dir = iniconf['core info']['sky_dir']
   
    org_fits = data_dir + "/" + iniconf['uncertainty calc']['org_fits']
    galfit_output_fits = data_dir + "/" + iniconf['core info']['galfit_output_fits']
    contamination_threshold = float(iniconf['uncertainty calc']['contaminant_frac'])
    overlap_frac_max = float(iniconf['uncertainty calc']['max_overlap'])

    if (contamination_threshold > .05) | (contamination_threshold <= 0) | (overlap_frac_max > .75) | (overlap_frac_max < 0):
        raise ValueError('Invalid Sky Slicing Parameters (contaminant threshold or overlap fraction')
     
    all_c = iniconf['core info']['cutout_region'].split(',')
    plot_sky = iniconf['uncertainty calc']['plot_sky_dist']


    #get header of org_fits 
    org_img = fits.open(org_fits)[0]
    org_header = org_img.header

    #load the appropriate slice of galfit model
    model_fits = fits.open(galfit_output_fits)
    model_slice = model_fits[2].data
    #shape of array is going to be 
    cutout_size_x = int(all_c[3]) - int(all_c[2]) + 1
    cutout_size_y = int(all_c[1]) - int(all_c[0]) + 1

    


    #open the fits file, calculate sigma-clipped statistics
    ref_data = fits.open(org_fits)[0].data
    imdim_x = ref_data.shape[0]
    imdim_y = ref_data.shape[1]
    im_mean, im_median, im_std = sigma_clipped_stats(ref_data, sigma = 3, maxiters = 5) 
     
    mask = np.zeros(ref_data.copy().shape)
    masked_image = np.where((ref_data > (im_median + 3*im_std)),1, mask)

    ### Code for finding best blank regions
    percentage_cut = contamination_threshold  * cutout_size_x*   cutout_size_y


    ## loop through and find frames where less than the percentage_cut number of pixels is occupied by bright sources
    best_frames = []
    sums = []
    for xposition in range(imdim_x - cutout_size_x):
        for yposition in range(imdim_y - cutout_size_y):
            im = masked_image[yposition:yposition+cutout_size_y,xposition:xposition+cutout_size_x]
        
            frame_sum = np.sum(im)
            if frame_sum < percentage_cut:
                best_frames.append([xposition,yposition])
                sums.append(frame_sum)
    best_frames = np.array(best_frames)
    ### sort the frames by their quality, clean up a bit 
    revised_best_frames_x = best_frames[:,0][np.argsort(sums)]
    revised_best_frames_y = best_frames[:,1][np.argsort(sums)]
    del best_frames
    best_frames2 = np.asarray([revised_best_frames_x ,revised_best_frames_y]).T

    ## remove overlaps from sorted frame list (more documentation will come later...)
    keepx = []
    keepy = []

    start_x = best_frames2[0][0]
    start_y = best_frames2[0][1]

    keepx.append(start_x)
    keepy.append(start_y)

    overlap_limit_x = (1-overlap_frac_max) * cutout_size_x
    overlap_limit_y = (1-overlap_frac_max) * cutout_size_y
 
    for [a,b] in best_frames2: 
    
        if (((np.abs(a - keepx) > overlap_limit_x).all()) | ((np.abs(b - keepy) > overlap_limit_y).all())):
            keepx.append(a)
            keepy.append(b)
        else: 
            continue

    joint = np.asarray([keepx,keepy]).T

    ## extract slices, add galfit model to each slice
    for i, [a,b] in enumerate(joint):
        
        new_sky_v1 = ref_data[a:a+cutout_size_x,b:b+cutout_size_y]
        
        new_sky = maskBrightSource(new_sky_v1) ### run code for interpolating brighter sources
      
        final_mock = new_sky + model_slice 
        temp_name = sky_dir + "/" + "new_skycut_%d.fits"%i

        #save this new fits file 
        # hdu = fits.PrimaryHDU(final_mock)
        fits.writeto(temp_name, final_mock,org_header,overwrite = True)

        #the corresponding .gal files for these fits file are created in run_unc_pipeline.py


    

    if plot_sky == "True":
        norm = ImageNormalize(ref_data, interval=ZScaleInterval(),stretch=LinearStretch())
        img_save = output_dir + "/" + "skyCutouts.png"
        fig,ax = plt.subplots(1,1,figsize = (8,8))
        ax = plt.gca()
        ax.imshow(ref_data, origin='lower', cmap='gray',norm=norm)
        for [a,b] in joint:
            rect = patches.Rectangle((a,b), cutout_size_x, cutout_size_y, linewidth= 2,alpha = 1 ,edgecolor='r', facecolor='none')
            ax.add_patch(rect)
        plt.savefig(img_save)
        print_stage("Sky Cutout Layout Available here : %s"%img_save,ch = "-")

    return 

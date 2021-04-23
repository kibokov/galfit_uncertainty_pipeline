import numpy as np 
from astropy.stats import sigma_clip
from astropy.io import fits
import random
import matplotlib.pyplot as plt

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


def bootstrap_sky(iniconf):
    '''
    Function that will generate fake sky cutouts 
    '''

    data_dir = iniconf['core info']['data_dir']
    output_dir = iniconf['core info']['output_dir']
    sky_dir = iniconf['core info']['sky_dir']


    org_fits = data_dir + "/" + iniconf['uncertainty calc']['org_fits']
    galfit_output_fits = data_dir + "/" + iniconf['core info']['galfit_output_fits']
    niter = int(iniconf['uncertainty calc']['niter'])
    all_c = iniconf['core info']['cutout_region'].split(',')
    plot_sky = iniconf['uncertainty calc']['plot_sky_dist']

    #get header of org_fits 
    org_img = fits.open(org_fits)[0]
    org_header = org_img.header

    #load the appropriate slice of galfit model
    model_fits = fits.open(galfit_output_fits)
    model_slice = model_fits[2].data
    #shape of array is going to be 
    rows = int(all_c[3]) - int(all_c[2]) + 1
    cols = int(all_c[1]) - int(all_c[0]) + 1

    #open the fits file
    pix_data = fits.open(org_fits)[0]
    all_pix = np.concatenate(pix_data.data)
    clip_pixs = sigma_clip(all_pix,sigma=3,maxiters=None,cenfunc=np.mean, masked=False, copy=False)

    if plot_sky == "True":
        img_save = output_dir + "/" + "sky.png"
        fig = plt.figure()
        plt.hist(clip_pixs,bins = 'sqrt')
        plt.axvline(x = 0,color = 'k',label = "pixel = 0")
        plt.legend()
        plt.savefig(img_save)
        print_stage("Sky pixel value distribution saved here : %s"%img_save,ch = "-")
    
    random.shuffle(clip_pixs)

    #the clip_pix array is the array of all the sky pixels. It should be quite Gaussian in nature
    #generate random array of integers 

    for i in range(niter):
        rand_inds = np.random.randint(len(clip_pixs)-1, size = (rows,cols))
        new_sky = clip_pixs[rand_inds]
        #we add this sky to the galfit model
        final_mock = new_sky + model_slice 
        sky_name = sky_dir + "/" + "new_skycut_%d.fits"%i

        #save this new fits file 
        # hdu = fits.PrimaryHDU(final_mock)
        fits.writeto(sky_name, final_mock,org_header,overwrite = True)

        #the corresponding .gal files for these fits file are created in run_unc_pipeline.py

    return 

    



    










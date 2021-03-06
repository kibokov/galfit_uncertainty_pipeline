'''
Script that goes through all the galfit results of new sky cutouts 
and stores the distribution of magnitudes of each modelled component 
'''
import glob
import numpy as np 
from astropy.io import fits
from generate_reg import GalfitComponent, GalfitResults

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

def compute_unc(iniconf):

    sky_dir = iniconf['core info']['sky_dir']
    data_dir = iniconf['core info']['data_dir']
    output_dir = iniconf['core info']['output_dir']
    comp_ident = data_dir + "/" + iniconf['uncertainty calc']['comp_ident']
    output_mag_file = output_dir + "/" + iniconf['uncertainty calc']['output_mag_file']
    galfit_output_fits = data_dir + "/" + iniconf['core info']['galfit_output_fits']

    all_sky_cuts = glob.glob(sky_dir + "/" + "*_output.fits")
    
    g = GalfitResults(galfit_output_fits)
    mag_zpt = float(g.input_magzpt)

    print_stage("The zero point magnitude used is %f"%mag_zpt)

    comp_data = np.loadtxt(comp_ident,dtype=int)
    comp_num = comp_data[:,0]
    comp_obj_id = comp_data[:,1]
    obj_num = np.max(comp_obj_id)

    #empty array initialized. This array will be populated with combined object magnitudes
    sky_files_num = int(len(all_sky_cuts))+1
    all_magnitudes = np.zeros(shape = (sky_files_num,obj_num))

    if np.min(np.bincount(comp_obj_id)[1:]) == 0:
        raise ValueError("recheck your comp_ident file. Appears that you have misnumbered and missed a number.")

    #we first compute the magnitude of the actual galfit model sitting in data_dir
    #read the model header for galfit output fits in data_dir
    org_model_data = fits.open(galfit_output_fits)
    org_model_header = org_model_data[2].header
    for on in range(1,obj_num+1):
        cn = comp_num[comp_obj_id == on]
        tot_flux_org = 0
        for cni in cn:
            magi = org_model_header['%d_MAG'%cni]
            mag_str = magi.split(" +/-")[0]
            mag_fl = float(mag_str.replace("*",""))
            #convert this mag to flux and append to list to be summed.
            flux = 10**(-0.4*(mag_fl - mag_zpt))
            tot_flux_org += flux

            #convert the total object flux back to magnitudes
            final_mag_org = mag_zpt - 2.5*np.log10(tot_flux_org)
            all_magnitudes[0,on-1] = final_mag_org

    for i,ski in enumerate(all_sky_cuts):
        #open the fits file and read the header for model info
        img = fits.open(ski)
        model_header = img[2].header
        for on in range(1,obj_num+1): #tot_obj_num   = [1,2,3,4, ...]
            cn = comp_num[comp_obj_id == on]
            tot_flux = 0
            for cni in cn:
                magi = model_header['%d_MAG'%cni]
                mag_str = magi.split(" +/-")[0]
                mag_fl = float(mag_str.replace("*",""))
                #convert this mag to flux and append to list to be summed.
                flux = 10**(-0.4*(mag_fl - mag_zpt))
                tot_flux += flux

            #convert the total object flux back to magnitudes
            final_mag = mag_zpt - 2.5*np.log10(tot_flux)
            all_magnitudes[i+1,on-1] = final_mag

    #check that all_magnitudes array is populated 
    if np.max(all_magnitudes) == 0:
        raise ValueError("Appears that one of the elements was not updated with correct magnitude.")

    #write this all_magnitudes array as a output file
    np.savetxt(output_mag_file,all_magnitudes,comments = "first row are magnitudes from original galfit model. Starting from row 1 are magnitudes with generated skies.")

    print_stage("All object magnitudes have been stored here : %s"%output_mag_file)

    return 

    
            





        




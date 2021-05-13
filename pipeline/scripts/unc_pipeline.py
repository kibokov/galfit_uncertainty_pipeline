import argparse
import numpy as np
import os
from configparser import ConfigParser, ExtendedInterpolation
import numpy as np
import glob
from tqdm import tqdm 
from gen_skys import bootstrap_sky, slice_sky
from compute_unc import compute_unc
from galshift import galshift
import concurrent.futures
from slice_images import slice_sky

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



def run_in_parallel(func, iter_input):
    '''
    running a function in parallel.

    Parameters:
    -----------
        func: function, the function to be parallelized
        iter_input: list, the list of function inputs to loop over
    Returns:
    -----------
        results: list, entire function output
    '''
    print(len(iter_input))
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = list(tqdm(executor.map(func,iter_input), total = len(iter_input))) 
    return results


# def run_gal(gpi,run_on_lipwig = False):
def run_gal(input_stuff=None):
    gpi = input_stuff['gpi']
    run_on_lipwig = input_stuff['run_on_lipwig']
    if run_on_lipwig == "False":
        os.system("./galfit " + gpi + " >> run_log.txt")
    if run_on_lipwig == "True":
        os.system("galfit " + gpi + " >> run_log.txt")
    return 


def unc_pipeline(iniconf):

    pipeline_dir = iniconf['core info']['pipeline_dir']
    sky_dir = iniconf['core info']['sky_dir']
    data_dir = iniconf['core info']['data_dir']
    # scripts_dir = iniconf['core info']['scripts_dir']
    psf_fits = iniconf['uncertainty calc']['psf_fits']

    lipwig = iniconf['uncertainty calc']['lipwig']
    con_file = data_dir + "/" + iniconf['uncertainty calc']['constraint_file']
    gal_log = iniconf['uncertainty calc']['print_gal_log']
    working_in_cutout = iniconf['core info']['cutout_frame']
    run_parallel = iniconf['uncertainty calc']['run_parallel']
    method = iniconf['uncertainty calc']['method']
    galfit_output_fits = data_dir + "/" + iniconf['core info']['galfit_output_fits']


    #first check if all the relevant files exist
    if not os.path.isfile(data_dir + "/" + psf_fits):
        raise ValueError('input PSF file {:s} does not exist!'.format(data_dir + "/" + psf_fits))
    if not os.path.isfile(galfit_output_fits):
        raise ValueError('input GalFit Model file {:s} does not exist!'.format(galfit_output_fits))
    if not os.path.isfile(con_file) and con_file.replace(data_dir + "/","") != "none":
        raise ValueError('input constraint file {:s} does not exist!'.format(con_file))


    #first clean all the files in the temp directory
    os.chdir(sky_dir)
    os.system('find . -name "*.fits" -type f -delete')
    os.system('find . -name "*.gal" -type f -delete')

    #clean all the galfit 
    os.chdir(pipeline_dir)
    os.system('find . -name "galfit.*" -type f -delete')

    #make a .gal using the output fits 
    galshift(iniconf,working_in_cutout=working_in_cutout)
    galfit_params = data_dir + "/" + "temp.gal"

    #############################

    ###########
    #run the new sky cutout generation script and generate new cutouts 
    if method == "bootstrap":
        bootstrap_sky(iniconf)
    if method == "interpolation":
        slice_sky(iniconf)

    print_stage("Skies have been generated")

    ###########

    file_names = glob.glob(sky_dir + "/" + "*.fits")

    if len(file_names) < 10:
        print_stage("WARNING: The number of skies found/generated are less than 10. A very small number of skies will not give robust statistics. You change the contaminant fraction or max overlap allowed to increase the number of skies.")
    all_gal_lines = open(galfit_params).readlines()

    #read all the .gal file created in temp dir
    for fi in file_names:
        fi_new = fi.replace(pipeline_dir + "/","")
        output_fi = fi_new.replace(".fits","") + "_output.fits"

        psf_file = data_dir + "/" + psf_fits
        psf_file_new = psf_file.replace(pipeline_dir+"/","")

        temp_lines = all_gal_lines
        new_gal = fi.replace(".fits",".gal")
        
        if con_file == "none":
            con_file_new = "none"
        else:
            con_file_new = con_file.replace(pipeline_dir+"/","")

        new_g = open(new_gal,"w+")
        #the paths here need to relative paths wrt to galfit script
        temp_lines[2] = 'A) ' + fi_new + '\t\t\t\t # <<<<<< file you want to fit\n'
        temp_lines[3] = 'B) ' + output_fi + '\t\t\t\t # <<<<<< output file name\n'
        temp_lines[5] = 'D) ' +  psf_file_new  + '\t\t\t\t # <<<<<< input PSF image and (optional) diffusion kernel \n'
        temp_lines[8] = 'G) ' +  con_file_new  + '\t\t\t\t # <<<<<< File with parameter constraints (ASCII file) \n'


        for tli in temp_lines:
            new_g.write(tli)
        new_g.close()

    #now run these individual galfit files
    all_gal_params = glob.glob(sky_dir + "/" + "*.gal")

    os.chdir(pipeline_dir)
    if run_parallel == "False":
        for gpi in tqdm(all_gal_params):
            if lipwig == "False":
                command1 = "./galfit " + gpi
            else:
                command1 = "galfit " + gpi
        
            if gal_log == "False":
                command2 = " >> run_log.txt"
            else:
                command2 = ""
            os.system(command1+command2)

    if run_parallel == "True":
        input_stuff = []
        for i in range(len(all_gal_params)):
            dicti = {"gpi": all_gal_params[i], "run_on_lipwig": "True"}
            input_stuff.append(dicti)

        run_in_parallel(run_gal,input_stuff)


    #now computing uncertainties 

    compute_unc(iniconf)

    #clean all the galfit 
    os.chdir(pipeline_dir)
    os.system('find . -name "galfit.*" -type f -delete')

    return 





    












    





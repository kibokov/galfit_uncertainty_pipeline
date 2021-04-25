'''
Script that creates region files based on galfit output files.

How to run this script?

$ python3 create_reg.py -fits galfit_output.fits

You can also give it the full path if file is in a different directory

$ python3 create_reg.py -fits /Users/radioactive/Desktop/data/galfit_output.fits

The galfit_output.fits is the multiextension cube fits file that galfit outputs once you run your model.

The output of this code should be a .reg file with the same file name as input. 
You can load this file as a region file into the original data image to look at your galfit model.

--------------------------------------------------------------------------------
The GalfitComponent object is based on astronomeralex's galfit-python-parser:
    https://github.com/astronomeralex/galfit-python-parser
Modified by Song Huang to include more features
The later modified by Katya Gozman to actually work correctly.
Further modified by Viraj Manwadkar and Will Cerny.
---------------------------------------------------------------------------------
'''

import re
import numpy as np
import os
from astropy.io import fits
from configparser import ConfigParser, ExtendedInterpolation
import argparse

def argument_parser():
    '''
    Function that parses the arguments passed while running a script

	fits : str, the multi extension fits file outputted by galfit
	for_cutout: str, True of False
    '''
    result = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # path to the config file with parameters and information about the run
    result.add_argument('-ini', dest='ini', type=str) 
    return result

def read_config_file(config_file=None):
    '''
    Function that reads the ini file

    Parameters:
    -------------
    config_file: str, path to the config file

    Returns:
    ------------
    iniconf: dict, dictionary of parameters in the config file

    '''

    if config_file is None:
        raise ValueError('input configuration file is not provided. Use -ini config_file_path to specify the config file')

    if not os.path.isfile(config_file):
        raise ValueError('input configuration file {:s} does not exist!'.format(config_file))

    iniconf = ConfigParser(interpolation=ExtendedInterpolation())
    iniconf.read(config_file)  
    return iniconf 

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


class GalfitComponent(object):
    """
    stores results from one component of the fit
    """
    def __init__(self,galfitheader,component_number):
        """
        takes in the fits header from HDU 3 (the galfit model) from a galfit output file
        and the component number to extract
        """
        #checks
        # print(component_number)
        assert component_number > 0
        assert "COMP_" + str(component_number) in galfitheader

        self.component_type = galfitheader["COMP_" + str(component_number)]
        self.component_number = component_number
        headerkeys = [i for i in galfitheader.keys()]
        comp_params = []

        for i in headerkeys:
      
            word = '^' + str(component_number) + '_' 
            r = re.compile(r'^%s'%word)
            if r.search(i) != None:
                comp_params.append(i)
                 
        # print(comp_params)
        for param in comp_params:
            val = galfitheader[param]
            #we know that val is a string formatted as 'result +/- uncertainty'
            #if val is fixed in GalFit, it is formatted as '[result]'
            paramsplit = param.split('_')
            
            # If there's some numerical error, should output a warning (*)
            
            if '[' in val:     #fixed parameter
                #val = val.translate(None,'[]*')
                val= val.translate({ord(c): None for c in '[]*'})
                #val=val.translate(string.maketrans('', ''), '[]*')
                setattr(self,paramsplit[1].lower(),float(val))
                #print(paramsplit[1].lower(), float(val))
                setattr(self,paramsplit[1].lower() + '_err',None)
            else:              #normal variable parameter
                #val = val.translate(None,'*').split()
                #val = val.translate(string.maketrans('', ''), '*')
                val= val.translate({ord(c): None for c in '*'}).split()
                setattr(self,paramsplit[1].lower(),float(val[0]))
                #print(paramsplit[1].lower(), float(val[0]))
                setattr(self,paramsplit[1].lower() + '_err',float(val[2]))

class GalfitResults(object):

    """
    This class stores galfit results information.
    Currently only does one component
    """

    def __init__(self, galfit_fits_file, hduLength=4, verbose=True):
        """
        Init method for GalfitResults.
        Take in a string that is the name of the galfit output fits file
        """
        hdulist = fits.open(galfit_fits_file)
        # Now some checks to make sure the file is what we are expecting
        
        #THESE LINES ONLY FOR 390, 814, 140, 105 filters!!!
        assert len(hdulist) == hduLength
        galfitmodel = hdulist[hduLength - 2]
        
        #galfitmodel = hdulist[0]
        galfitheader = galfitmodel.header
        galfit_in_comments = False
        for i in galfitheader['COMMENT']:
            galfit_in_comments = galfit_in_comments or "GALFIT" in i
        assert True == galfit_in_comments
        assert "COMP_1" in galfitheader
        # Now we've convinced ourselves that this is probably a galfit file

        self.galfit_fits_file = galfit_fits_file
        # Read in the input parameters
        self.input_initfile = galfitheader['INITFILE']
        self.input_datain = galfitheader["DATAIN"]
        self.input_sigma = galfitheader["SIGMA"]
        self.input_psf = galfitheader["PSF"]
        self.input_constrnt = galfitheader["CONSTRNT"]
        self.input_mask = galfitheader["MASK"]
        self.input_magzpt = galfitheader["MAGZPT"]

        # Fitting region
        fitsect = galfitheader["FITSECT"]
        fitsect = re.findall(r"[\w']+", fitsect)
        self.box_x0 = fitsect[0]
        self.box_x1 = fitsect[1]
        self.box_y0 = fitsect[2]
        self.box_y1 = fitsect[3]

        # Convolution box
        convbox = galfitheader["CONVBOX"]
        convbox = convbox.split(",")
        self.convbox_x = convbox[0]
        self.convbox_y = convbox[1]

        # Read in the chi-square value
        self.chisq = galfitheader["CHISQ"]
        self.ndof = galfitheader["NDOF"]
        self.nfree = galfitheader["NFREE"]
        self.reduced_chisq = galfitheader["CHI2NU"]
        self.logfile = galfitheader["LOGFILE"]

        # Find the number of components
        num_components = 1
        while True:
            if "COMP_" + str(num_components + 1) in galfitheader:
                num_components = num_components + 1
            else:
                break
        self.num_components = num_components
        print_stage("Number of comps in your galfit model = " + str(self.num_components),ch = "-")
        for i in range(1, self.num_components + 1):
            setattr(self, "component_" + str(i),
                    GalfitComponent(galfitheader, i),
                    )
            #print(self.component_number)
        hdulist.close()


def coord_transform(old_c,shift_c):
	'''
	Function that does a translational coordinate shift

	Parameters:
	------------
	old_c : str, original coordinate
	shift_c : str/float, shift to perform

	Notes:
	-----------
	The input coordinates are strings because they are read from the header of the galfit output fits file.
	'''

	return str(float(old_c) - float(shift_c))


def generate_reg(iniconf):

    #read the galfit output file 
    path =  iniconf['core info']['galfit_output_fits']  
    cutout = iniconf['reg creation']['for_cutout']
    reg_name = iniconf['reg creation']['reg_file_name']
    data_dir = iniconf['core info']['data_dir']
    output_dir = iniconf['core info']['output_dir']

    all_c = iniconf['core info']['cutout_region'].split(',')
    
    if path[-5:] != ".fits":
        raise ValueError('aborting...input file is not .fits file : %s'%path)

    if reg_name[-4:] != ".reg":
        raise ValueError('aborting...input file is not .reg file : %s'%path)

    if cutout != "True" and cutout != "False":
        raise ValueError('aborting...invalid cutout input : %s'%cutout)

    final_fits_path = data_dir + "/" + path

    print_stage('This galfit output file is being read : %s'%final_fits_path,ch = "-")

    g = GalfitResults(final_fits_path)

    #check if inputted coordiantes for box and those read from header match
    if float(all_c[0]) != float(g.box_x0) or float(all_c[1]) != float(g.box_x1)  or float(all_c[2]) != float(g.box_y0)  or float(all_c[3]) != float(g.box_y1):
        raise ValueError('recheck inputted cutout region coordinates. They do not agree with those read from galfit output header file.')

    #path of the region file to be created
    output_file = output_dir + "/" + reg_name

    with open(output_file, 'w') as f:
        f.write('global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1\nimage\n')
        angle = '90'
        #calculate the height and width of the box
        width = str(float(g.box_x1)-float(g.box_x0)+1)
        height = str(float(g.box_y1)-float(g.box_y0)+1)
        #calculate the center of box
        center_x = str(0.5*(float(g.box_x0)+float(g.box_x1)))
        center_y = str(0.5*(float(g.box_y0)+float(g.box_y1)))

        if cutout == "True":
            center_x_new = coord_transform(center_x,float(g.box_x0)-1)
            center_y_new = coord_transform(center_y,float(g.box_y0)-1)
            
            f.write('box(%s, %s, %s, %s, %s)\n'%(center_x_new,center_y_new,height,width,angle) )
        else: 
            #write the box to .reg file
            f.write('box(%s, %s, %s, %s, %s)\n'%(center_x,center_y,height,width,angle) )

        for key in g.__dict__.keys():
            if 'component_' in key:
                # print(type(key), key)
                comp = getattr(g, key)
                #ignore sky, draw circle for psf and ellipse for all other comps
                if comp.component_type != 'sky':

                    if cutout == "True":
                    	comp_x = coord_transform(comp.xc,float(g.box_x0)-1)
                    	comp_y = coord_transform(comp.yc,float(g.box_y0)-1)
                    else:
                        comp_x = comp.xc
                        comp_y = comp.yc

                    if comp.component_type == 'psf':
                        f.write('circle(%s, %s, 3) # color=red width=2 text={%s}\n'%(comp_x,comp_y, comp.component_number))
                    else:
                        f.write('ellipse(%s, %s, %s, %s, %s) # width = 2 text = {%s}\n' %(comp_x,comp_y, comp.ar*comp.re, comp.re, comp.pa, comp.component_number))

    print_stage('The region file has been generated : %s'%output_file,ch = "-")


    return

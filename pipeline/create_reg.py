import argparse
import numpy as np
import os
from configparser import ConfigParser, ExtendedInterpolation
import sys


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

def argument_parser():
    '''
    Function that parses the arguments passed while running a script

	fits : str, the multi extension fits file outputted by galfit
	for_cutout: str, True of False
    '''
    result = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # path to the config file with parameters and information about the run
    result.add_argument('-ini', dest='ini', type=str,default="galfit_pipeline.ini") 
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


if __name__ == '__main__': 

    # read in command line arguments
    args = argument_parser().parse_args()
    # read parameters and information from the run config file 
    iniconf = read_config_file(config_file=args.ini)
    scripts_dir = iniconf['core info']['scripts_dir']
    sys.path.insert(1,scripts_dir)
    from generate_reg import generate_reg
    print_stage("The following ini file is being read : " + str(args.ini))

    #run the region file generator pipeline
    generate_reg(iniconf)

'''
Script that will create a new galfit parameters file which has shifted the coordinates.
The new origin will be the bottom left corner of cutout box. 
'''

from generate_reg import GalfitComponent, GalfitResults

galfit_feedme = '''================================================================================
# IMAGE and GALFIT CONTROL PARAMETERS
A) %s  # <<<<<< file you want to fit
B) %s   # <<<<<< output file name
C) none                # Sigma image name (made from data if blank or "none") 
D) %s                  # Input PSF image and (optional) diffusion kernel
E) 1                   # PSF fine sampling factor relative to data 
F) none                # <<<<<< mask image (0=use, 1=ignore)
G) %s                    # <<<<<< File with parameter constraints (ASCII file) 
H) %s %s %s %s  # <<<<<< region in A) for fit, as x1 x2 y1 y2 
I) %s %s             # size of the convolution
J) %s              # <<<<<< Magnitude photometric zeropoint * 
K) 0.16  0.16       # Image scale in arcsec/pix
O) regular             # Display type (regular, curses, both)
P) 0                   # <<<<<< Choose: 0=optimize, 1=model, 2=imgblock, 3=subcomps **

================================================================================
'''


galfit_comp = '''
 0) %s             # Object type
 1) %s  %s  1 1    # position x, y        [pixel]
 3) %s      1       # total magnitude    
 4) %s     1       #     R_e              [Pixels]
 5) %s       1       # Sersic exponent (deVauc=4, expdisk=1)  
 9) %s       1       # axis ratio (b/a)   
10) %s       1       # position angle (PA)  [Degrees: Up=0, Left=90]
 Z) 0                  #  Skip this model in output image?  (yes=1, no=0)
'''

sky_comp = '''
0) sky                    #  Component type
1) %s        1          #  Sky background at center of fitting region [ADUs]
2) 0.000e+00      0       #  dsky/dx (sky gradient in x)     [ADUs/pix]
3) 0.000e+00      0       #  dsky/dy (sky gradient in y)     [ADUs/pix]
Z) 1                      #  Skip this model in output image?  (yes=1, no=0)
================================================================================
'''

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

	return str(float(old_c) - int(shift_c))

def galshift(iniconf,working_in_cutout="False"):
    data_dir = iniconf['core info']['data_dir']
    galfit_output_fits = data_dir + "/" + iniconf['core info']['galfit_output_fits']
    galfit_params = "temp.gal"
    galfit_con = data_dir + "/" + iniconf['uncertainty calc']['constraint_file']

    g = GalfitResults(galfit_output_fits)

    new_gal_path = data_dir + "/" + galfit_params

    with open(new_gal_path,"w") as new_gal:
        #read the zeropoint magnitude, pixel scale
        #also read the size of the convolution box
        conv_x = g.convbox_x
        conv_y = g.convbox_y
        mag_zpt = g.input_magzpt

        if working_in_cutout == "False":
            new_x1 = str(int(g.box_x1) - int(g.box_x0)+1)
            new_y1 = str(int(g.box_y1) - int(g.box_y0)+1)
            #new_x1, new_y1 will also be values for the convolution box size
            new_gal.write(galfit_feedme%(g.input_datain, g.galfit_fits_file,g.input_psf, galfit_con ,"1",new_x1,"1",new_y1,conv_x, conv_y, mag_zpt))
        else:
            conv_x = int(g.box_x1) - int(g.box_x0) + 1
            conv_y = int(g.box_y1) - int(g.box_y0) + 1
            new_gal.write(galfit_feedme%(g.input_datain, g.galfit_fits_file,g.input_psf, galfit_con ,g.box_x0,g.box_x1,g.box_y0,g.box_y1,conv_x,conv_y, mag_zpt))

        for key in g.__dict__.keys():
            if 'component_' in key:
                comp = getattr(g, key)
                if comp.component_type != 'sky':
                    if float(comp.mag) > 25:
                        comp_mag = 25
                    else:
                        comp_mag = comp.mag

                    if working_in_cutout == "False":
                        new_x = coord_transform(comp.xc,int(g.box_x0)-1)
                        new_y = coord_transform(comp.yc,int(g.box_y0)-1)
                        new_gal.write(galfit_comp%(comp.component_type,new_x,new_y,comp_mag,comp.re,comp.n,comp.ar,comp.pa   ) )
                    else:
                        new_gal.write(galfit_comp%(comp.component_type,comp.xc,comp.yc,comp_mag,comp.re,comp.n,comp.ar,comp.pa   ) )
                        
                else:
                    new_gal.write(sky_comp%(comp.sky))

    new_gal.close()
    return 

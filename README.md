# GALFIT Uncertainty and Reg File Pipeline

The pipeline that calculates magnitude uncertaintines and model region file from the GALFIT model. This code was built by Viraj Manwadkar and Will Cerny (Field Course, Winter-Spring 2021); we owe thanks to Ezra Sukay and Kaiya Merz for writing the original GalFit uncertainty code upon which this version is loosely based.

In particular, this new version implements an automated algorithm for selection of nearly-blank regions of sky (rather than manual, as was the case before for), and then runs a 2D Gaussian Kernel for interpolation of any lingering bright sources (of which there are very few) with noise, so as to avoid these sources biasing the GalFit models. We also allow greater control over the entire process by implementing a main script + config.ini framework, which means that you can tweak many parameters about this process without editing any subfiles. There are also a few bonus features, like parallelization of running multiple GalFit models simultaneously.

## Dependencies
This code will require a number of standard python packages, including:
* Standard utilities: numpy, matplotlib
* .fits file handling: astropy, astropy.io
* Shell/Command Line handling: re, shutil, os, configparser, glob

These can all be installed with a standard <code> pip install PACKAGE</code>, although we note that many of these come with standard Anaconda distributions.

## Setting up the Pipeline

These are the instructions to setup up the pipeline.

1. Clone the repository onto your local machine by running below command in the directory of choice
```
> git clone https://github.com/kibokov/galfit_uncertainty_pipeline.git
```
2. In the ```pipeline``` directory, open the ini file (file with extension ```.ini```) and change the *pipeline_dir*. This will be the path pointing to your ```pipeline``` directory in the cloned repositroy.
 
## Directory Structure 

The ```data``` directory will contain all files used to run the pipeline. The ```outputs``` directory contains all pipeline outputs (eg. the region file, magnitude outputs txt etc.). The ```scripts``` directory contains all the pipeline code. The ```sky_files``` directory is where all the "new sky cutouts + galfit model" fits file are stored (along with their corresponding .gal file). GalFit is then run on these fits files in ```sky_files``` directory to then compute the uncertainity. 

The ```run_unc.py``` is the python script that will run the entire pipeline. The ```galfit_pipeline.ini``` is the ini file that contains all information for pipeline. More detailed comments about what each parameter in the ini file means are given in the file itself

## Running the Region File Pipeline

1. Make sure the *pipeline_dir* in ```galfit_pipeline.ini```  is the correct path. Make sure all the correct info is filled in ```[core info]``` and ```[reg creation]``` sections of ini file.  

2. Run the following command inside the ```pipeline``` directory,
```
> python3 create_reg.py
```
The above command by default reads the ```galfit_pipeline.ini``` file. However, in case you change the name or wish to provide a different one, you can specify that through the ini fiag as below
```
> python3 create_reg.py -ini new_name.ini
```
3. The region file will be created in the ```outputs``` directory. 


## Running the Uncertainity Pipeline

1. Make sure the *pipeline_dir* in ```galfit_pipeline.ini```  is the correct path. Make sure all the correct info is filled in ```[core info]``` and ```[uncertainty calc]``` sections of ini file.  

2. In the ```data``` directory, add your Multi-Extension Cube fits that GalFit outputs, the PSF fits (the slice), the constraint file, the original data fits, and a text file (called comp_ident) that contains the mapping between GalFit component number and object number in the field. After this, you will have to make the relevant changes in the ini file so as to provide the corrrect file names. 

3. In ini file, choose the correct method for background sky generation. We will be using the *interpolation* method. Note that a separate method called *bootstrap* has also been implemented, but we will not be using it for uncertainty calculations and was implemented for experimention purposes.

4. Run the following command inside the ```pipeline``` directory to run the pipeline.
```
> python3 run_unc.py
```
The above command by default reads the ```galfit_pipeline.ini``` file. However, in case you change the name or wish to provide a different one, you can specify that through the ini fiag as below
```
> python3 create_reg.py -ini new_name.ini
```
5. The ```output_mag_file``` file will be created in the ```outputs``` directory. The first row contains the magntudes of the original GalFit model you made. The following rows are for each sky generated. The columns are for each *object* (not component) in the field. Based on the ```comp_ident``` file, this pipeline combines the flux of the GalFit components of an object and returns the total magnitude. Refer to Note #4 for more on this.

## Testing this Pipeline

There is some test data sitting in the pipeline already. Once you clone this respository, you can see if this pipeline is working by running the above command. 

## Premise of the Uncertainty Calculation

Broadly speaking, the goal of the pipeline is to derive systematic modelling uncertainties from GalFit by taking your best-fit Galfit model and "injecting" it into (nearly-) blank regions of sky and re-running Galfit to see whether the difference in background causes a difference in the resulting magnitudes. This produces a distribution of magnitudes for each component from which we can use the standard deviation as one part of the modelling systematic uncertainty. 

In more detail, the code to calculate uncertainties (run through the main run_unc_pipeline, but stored within scripts/slice_images.py) works as follows:

1. Generate a mask of 3-sigma bright sources within your .fits image frame for a given filter band (eg, one of g,r,z for DECaLS)
2. Find regions of your image frame where the least number of pixels are covered by the mask (ie, least number of bright sources). Each region is the same size as the GalFit modelling region you specify in the .ini configuration file. The user can set a threshold in the .ini file for what percentage of each region can be occupied by a bright source. We find that setting this as 1% or .05% works well.  Because the number of blank regions is often limited by space on the frame, we allow for some overlap, set by the max_overlap parameter in the .ini file. For illustration, setting this parameter to .75 means 75% overlap is allowed. This type of change dramatically changes the number of regions that the algorithm will find, so its a compromise between (a) wanting to reduce overlap so each blank region is more statistically independent and (b) needing enough blank regions to ultimately get a good distribution of magnitudes. You can visually inspect the results -- see note 3.
3. For each identified blank region, create a new mask identifying 3-sigma bright pixels *in that region*. Mask these as np.nan, then run astropy's 2DGaussianKernel to interpolate these gaps with the local sky background. We run this twice, once with a larger kernel, and once with a smaller kernel, in hopes of capturing bright sources on these scales. These can be fine-tuned in slice_images.py  (but not yet in the config file)
4. Add the best-fit GalFit model to the (interpolated) slices of sky from Step 2-3. 
5. Re-run galfit on each of these slices.
6. Calculate magnitudes from the GalFit results for each physical object (NOT each component; this is what the comp_ident file is for)

## Notes

Some important notes 

1. To be explicitly clear, *you should only ever have to run one of these two python files: ```run_unc.py``` or ```create_reg.py``` file. Trying to run individual files in the ```scripts``` folder will not do anything, by design.*
2. If you choose the option ```print_gal_log = False```, all the GalFit output will be redirected to the ```run_log.txt``` file. After a few pipeline runs, that file will tend to become quite large. So do delete that txt file once in a while so as to make sure it does not get very large. 

3. You will notice that the outputs directory contains some other files as well. The ```skyCutouts.png``` file shows the image of all the sky regions the algorithm detects to interpolate. These are skies that have very little bright object contamination. 

4. The way total magnitude of an object is computed is as follows. 
```python
tot_flux = 0 
mag_zpt = #zero point magnitude. 
for component_i in components:
    mag = #read the magnitude of component_i from header
    flux = 10**(-0.4*(mag - mag_zpt))
    tot_flux += flux
    
final_mag = mag_zpt - 2.5*np.log10(tot_flux)
```
The zeropoint is automatically read from your galfit config files (fixing an earlier error where it was assumed to be 31.169).


5. For some OS, the galfit executable might not be downloading properly while cloning it from github. So a good idea is to replace the galfit executable from the cloned version with the version you already have on your machine. For Mac OS, i do not think this is an issue. However, for Linux this will be an issue.

5. When plotting the histogram of magnitudes, extract the columns from the final text file. Each column corresponds to a object. The first row is for the magnitudes from your original galfit model. Rest all rows are for the fake skies generated. 



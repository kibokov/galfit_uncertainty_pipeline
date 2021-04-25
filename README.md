# GALFIT Uncertainty and Reg File Pipeline

The pipeline that calculates magnitude uncertaintines and model region file from the GALFIT model.

## Dependencies
This code will require a number of standard python packages, including <code>numpy<code>, <code>astropy<code>,<code>astropy.io<code>,<code>matplotlib<code>

## Directory Structure 

The ```data``` direcotory will contain all files used to run the pipeline. The ```outputs``` directory contains all pipeline outputs (eg. the region file, magnitude outputs txt etc.). The ```scripts``` directory contains all the pipeline code. The ```sky_files``` directory is where all the "new sky cutouts + galfit model" fits file are stored (along with their corresponding .gal file). GALFIT is then run on these fits files in ```sky_files``` directory to then compute the uncertainity. 

The ```run_unc.py``` is the python script that will run the entire pipeline. The ```galfit_pipeline.ini``` is the ini file that contains all information for pipeline. More detailed comments about what each parameter in the ini file means are given in the file itself

## Running the Pipeline

The .ini file in the pipeline directory contains all the information neded to run this pipeline. You will need to make the relevant changes in the .ini file when running the pipeline on your machine. The 

More detailed steps are listed below:

1. In the data directory, add your Multi-Extension Cube fits that galfit outputs, the PSF fits (the slice), the constraint file, the original data fits, and a text file (called comp_ident) that contains the mapping between GALFIT component number and object number in the field. After this, you will have to make the relevant changes so as to provide the corrrect file names. 

2. In ini file,  choose the correct method for background sky generation. We will be using the **interpolation** method. 

3. Run the following command inside the pipeline directory to run the pipeline.
```
> python3 run_unc_pipeline.py -ini galfit_pipeline.ini
```

## Testing this Pipeline

There is some test data sitting in the pipeline already. Once you clone this respository, you can see if this pipeline is working by running the above command. 

## Uncertainty Calculation

The way we calculate uncertainties ..... Will you can fill this in

explain the contaminant fraction and max_overlap parameters 

## Notes

Some important notes 

1. If you choose the option ```print_gal_log = False```, all the GALFIT output will be redirected to the ```run_log.txt``` file. After a few pipeline runs, that file will tend to become quite large. So do delete that txt file once in a while so as to make sure it does not get very large. 

2. You will notice that the outputs directory contains some other files as well. The ```skyCutouts.png``` file shows the image of all the sky regions the algorithm detects to interpolate. These are skies that have very little bright object contamination. 

3. 

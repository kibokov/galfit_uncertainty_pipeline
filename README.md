# galfit_pipeline

This pipeline that calculates the uncertainties in a galfit model. 


## Running the Pipeline

Follow the below steps to run the pipeline

1. In the data directory, add your Multi-Extension Cube fits that galfit outputs, the PSF fits (the slice), the constraint file, the original data fits, and a text file (called comp_ident) that contains the mapping between GALFIT component number and object number in the field



Run the following command to run this pipeline. 
```
> python3 scripts/run_unc_pipeline.py -ini galfit_pipeline.ini
```
The galfit_pipeline.ini file is the configuration file that contains all the useful information for running the pipeline. Detailed comments are given in the .ini file. 

## Testing this Pipeline

If you hope to see if this pipeline runs smoothly on your machine, you can run the pipeline using the above command without changing any of the ini files. There is some test data here that it uses for running. If it runs smoothly then there should be no issue!




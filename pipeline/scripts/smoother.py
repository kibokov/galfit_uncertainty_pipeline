from astropy.io import fits
import matplotlib.pyplot as plt 
from astropy.visualization.stretch import SinhStretch, LinearStretch
from astropy.visualization import ImageNormalize
from astropy.visualization import ZScaleInterval
import matplotlib.patches as patches
import numpy as np
from astropy.stats import sigma_clipped_stats
from scipy import spatial
from astropy.convolution import Gaussian2DKernel, interpolate_replace_nans


def maskBrightSource(ref_data):
    im_mean1, im_median1, im_std1 = sigma_clipped_stats(ref_data, sigma = 3, maxiters = 5) 
    new_im1 = np.where((ref_data > (im_median1 + 3*im_std1)),np.nan, ref_data)
    
    
    kernel1 = Gaussian2DKernel(x_stddev= 8, y_stddev = 8)
    fixed_image1 = interpolate_replace_nans(new_im1, kernel1)
    
    
    im_mean2, im_median2, im_std2 = sigma_clipped_stats(fixed_image1, sigma = 3, maxiters = 5) 
    new_im2 = np.where((fixed_image1 > (im_median2 + 3*im_std2)),np.nan, fixed_image1)
    

    kernel2 = Gaussian2DKernel(x_stddev= 4, y_stddev = 4)
    fixed_image2 = interpolate_replace_nans(new_im2, kernel2)
    
    
    return fixed_image2

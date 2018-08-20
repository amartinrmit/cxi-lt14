"""
cxilt14py
- Analysis scripts for performing angular correlation analysis on the cspad detector @ CXI @ LCLS

correlation.py - calculate angular correlation function

September 2018

authors: Andrew Martin (andrew.martin@rmit.edu.au)
         

"""

import numpy as np
import scipy.ndimage as sdn


class angular_correlation:

    
    def polar_plot( self,data, nr, nth, rmin, rmax, thmin, thmax, cenx, ceny ):

        # r and theta arrays
        rarr = np.outer( np.arange(nr)*(rmax-rmin)/float(nr) + rmin, np.ones(nth) )
        tharr = np.outer( np.ones(nr), np.arange(nth)*(thmax-thmin)/float(nth) + thmin)
        
        newx = rarr*np.cos( tharr ) + cenx
        newy = rarr*np.sin( tharr ) + ceny
        
        print "debug",  newx.flatten().shape, newx.flatten()[:5]
        newdata = sdn.map_coordinates( data, [newx.flatten(), newy.flatten()], order=3 )

        return newdata.reshape( nr, nth )

    def polarplot_angular_correlation( self, polar, polar2=None):

        fpolar = np.fft.fft( polar, axis=2 )

        if polar2 != None:
            fpolar2 = np.fft.fft( polar2, axis=2)
        else:
            fpolar2 = fpolar

        out = np.fft.ifft( fpolar2.conjugate() * fpolar )
        
        return out

        
    def apply_mask( self, func, mask ):
        return func*mask


    def correct_mask_correlation( self, corr, maskcorr ):
        imask = np.where( maskcorr != 0 )
        corr[imask] *= 1.0/maskcorr[imask]
        return corr

    #    
    # pairwise correlation of (flattened) arrays
    #
    # not for angular correlations; good for correlation of mean asic values
    #
    def allpixel_correlation( self, arr1, arr2 ):
        out = np.outer( arr1.flatten(), arr2.flatten() )
        return out

#    def gaussian_filter_correlation( self, corr, qsig, thsig ):
        
        # linspace for q and th values... 
        # then turn that into guassian function
        # then call convoluation function
